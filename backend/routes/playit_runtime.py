import docker
import httpx
import logging
import time
from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from config import PLAYIT_AGENT_IMAGE
from database import get_db
from models.server import Server
from models.user import User
from utils.docker_client import get_docker_client
from utils.security import get_current_user


router = APIRouter(prefix="/api/servers", tags=["playit-runtime"])

PLAYIT_API_BASE = "https://api.playit.gg"


class PlayitRuntimeLinkRequest(BaseModel):
    agent_id: str | None = Field(default=None, max_length=128)
    agent_secret_key: str = Field(min_length=1, max_length=255)
    saved_tunnel_id: str | None = Field(default=None, max_length=128)
    saved_domain: str | None = Field(default=None, max_length=255)


def docker_client():
    return get_docker_client()


def server_container_name(server_id: int) -> str:
    return f"mc-panel-{server_id}"


def playit_container_name(server_id: int) -> str:
    return f"mc-playit-{server_id}"


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def get_server_for_user(server_id: int, db: Session, user: User) -> Server:
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


def playit_container_running(server_id: int) -> bool:
    try:
        container = docker_client().containers.get(playit_container_name(server_id))
        return container.status == "running"
    except DockerNotFound:
        return False
    except Exception:
        return False


def stop_playit_container(server_id: int) -> None:
    try:
        docker_client().containers.get(playit_container_name(server_id)).remove(force=True)
    except DockerNotFound:
        pass
    except Exception:
        pass


def get_object_id(value):
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        object_id = value.get("id")
        if isinstance(object_id, str):
            return object_id
    return None


def pick_tunnel_address(tunnel: dict | None) -> str:
    if not tunnel:
        return ""
    alloc_data = (tunnel.get("alloc") or {}).get("data") or {}
    return (
        str(tunnel.get("display_address") or "").strip()
        or str(tunnel.get("assigned_domain") or "").strip()
        or str(tunnel.get("custom_domain") or "").strip()
        or str((tunnel.get("domain") or {}).get("value") or "").strip()
        or str(alloc_data.get("assigned_domain") or "").strip()
        or str(alloc_data.get("address") or "").strip()
        or str(alloc_data.get("ip_hostname") or "").strip()
        or str(tunnel.get("connect_address") or "").strip()
        or str(tunnel.get("address") or "").strip()
    )


def find_matching_tunnel(tunnels, tunnel_id: str | None, server_port: int):
    if not isinstance(tunnels, list):
        return None

    for tunnel in tunnels:
        if not isinstance(tunnel, dict):
            continue
        port_from_config = None
        agent_config = tunnel.get("agent_config") or {}
        fields = agent_config.get("fields") or []
        if isinstance(fields, list):
            for field in fields:
                if isinstance(field, dict) and field.get("name") == "local_port":
                    port_from_config = field.get("value")
                    break

        if (
            str(get_object_id(tunnel.get("id")) or "") == str(tunnel_id or "")
            or int(tunnel.get("local_port") or 0) == server_port
            or int(port_from_config or 0) == server_port
        ):
            return tunnel

    return None


def call_agent_api(secret_key: str, path: str, body: dict | None = None) -> dict:
    try:
        response = httpx.post(
            f"{PLAYIT_API_BASE}{path}",
            headers={
                "Authorization": f"Agent-Key {secret_key.strip()}",
                "Content-Type": "application/json",
            },
            json=body or {},
            timeout=20,
        )
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": f"Failed to contact Playit agent API: {exc}"}

    text = response.text
    try:
        parsed = response.json() if text else None
    except ValueError:
        parsed = None

    if response.status_code >= 400:
        return {
            "ok": False,
            "detail": f"Playit agent API request failed with status {response.status_code}.",
            "parsed": parsed,
        }

    if not isinstance(parsed, dict):
        return {"ok": False, "detail": "Playit agent API returned invalid JSON.", "parsed": parsed}

    status = parsed.get("status")
    if status == "success":
        return {"ok": True, "data": parsed.get("data"), "parsed": parsed}

    if status == "fail":
        data = parsed.get("data")
        detail = data if isinstance(data, str) else (data or {}).get("error") or (data or {}).get("message") or str(data)
        return {"ok": False, "detail": detail or "Playit agent API returned a failure status.", "parsed": parsed}

    if status == "error":
        data = parsed.get("data") or {}
        detail = data.get("message", {}).get("path") if isinstance(data.get("message"), dict) else data.get("message")
        detail = detail or data.get("type") or parsed.get("message") or parsed.get("error")
        return {"ok": False, "detail": detail or "Playit agent API returned an error status.", "parsed": parsed}

    return {"ok": False, "detail": "Playit agent API returned an unknown response format.", "parsed": parsed}


def resolve_agent_id(secret_key: str, fallback_agent_id: str | None = None) -> str | None:
    for _ in range(5):
        for path in ("/agents/rundata", "/v1/agents/rundata"):
            result = call_agent_api(secret_key, path, {})
            if result.get("ok"):
                data = result.get("data") or {}
                agent_id = data.get("agent_id") or fallback_agent_id
                if agent_id:
                    return str(agent_id)
        time.sleep(1)
    return fallback_agent_id


def ensure_playit_tunnel(server: Server, user: User) -> tuple[str | None, str | None, str | None]:
    if not user.playit_agent_secret:
        return server.playit_tunnel_id, server.playit_domain, "Missing Playit agent secret."

    resolved_agent_id = resolve_agent_id(user.playit_agent_secret, user.playit_agent_id)
    user.playit_agent_id = resolved_agent_id
    if not resolved_agent_id:
        return server.playit_tunnel_id, server.playit_domain, "Playit agent is not ready yet."

    if server.playit_tunnel_id:
        run_data_v1 = call_agent_api(user.playit_agent_secret, "/v1/agents/rundata", {})
        if run_data_v1.get("ok"):
            tunnel = find_matching_tunnel((run_data_v1.get("data") or {}).get("tunnels"), server.playit_tunnel_id, server.port)
            domain = pick_tunnel_address(tunnel)
            if domain:
                return server.playit_tunnel_id, domain, None
        return server.playit_tunnel_id, server.playit_domain, None

    legacy_create = call_agent_api(
        user.playit_agent_secret,
        "/tunnels/create",
        {
            "name": f"EnderPanel - {server.name}"[:60],
            "tunnel_type": "minecraft-java",
            "port_type": "tcp",
            "port_count": 1,
            "origin": {
                "type": "agent",
                "data": {
                    "agent_id": resolved_agent_id,
                    "local_ip": "127.0.0.1",
                    "local_port": server.port,
                },
            },
            "enabled": True,
            "alloc": None,
            "firewall_id": None,
            "proxy_protocol": None,
        },
    )

    tunnel_result = legacy_create
    if not legacy_create.get("ok"):
        v1_create = call_agent_api(
            user.playit_agent_secret,
            "/v1/tunnels/create",
            {
                "ports": {"type": "tunnel-type", "details": "minecraft-java"},
                "origin": {
                    "type": "agent",
                    "data": {
                        "agent_id": resolved_agent_id,
                        "config": {
                            "fields": [
                                {"name": "local_ip", "value": "127.0.0.1"},
                                {"name": "local_port", "value": str(server.port)},
                            ]
                        },
                    },
                },
                "enabled": True,
                "alloc": None,
                "name": f"EnderPanel - {server.name}"[:60],
                "firewall_id": None,
            },
        )
        if v1_create.get("ok"):
            tunnel_result = v1_create
        else:
            return None, None, f"legacy: {legacy_create.get('detail')}; v1: {v1_create.get('detail')}"

    tunnel_id = get_object_id(tunnel_result.get("data"))
    domain = ""
    for path in ("/v1/agents/rundata", "/agents/rundata"):
        run_data = call_agent_api(user.playit_agent_secret, path, {})
        if run_data.get("ok"):
            tunnels = (run_data.get("data") or {}).get("tunnels") or []
            tunnel = find_matching_tunnel(tunnels, tunnel_id, server.port)
            logger.warning("playit rundata path=%s tunnel_id=%s tunnel=%s", path, tunnel_id, tunnel)
            domain = pick_tunnel_address(tunnel)
            if domain:
                break

    return tunnel_id, domain or None, None


def start_playit_container(server_id: int, agent_secret: str) -> None:
    client = docker_client()
    server_container = client.containers.get(server_container_name(server_id))
    server_container.reload()
    if server_container.status != "running":
        raise RuntimeError("Server must be running before Playit can attach")

    stop_playit_container(server_id)
    client.containers.run(
        PLAYIT_AGENT_IMAGE,
        name=playit_container_name(server_id),
        detach=True,
        network_mode=f"container:{server_container_name(server_id)}",
        restart_policy={"Name": "unless-stopped"},
        environment={"SECRET_KEY": agent_secret},
        labels={"enderpanel.playit": "true", "enderpanel.server_id": str(server_id)},
    )


def build_payload(server: Server, user: User) -> dict:
    linked = bool(server.playit_enabled and user.playit_agent_secret)
    return {
        "linked": linked,
        "enabled": bool(server.playit_enabled),
        "server_running": server.status == "running",
        "agent_running": linked and playit_container_running(server.id),
        "agent_id": user.playit_agent_id if linked else None,
        "agent_secret_masked": mask_secret(user.playit_agent_secret) if linked else None,
        "saved_domain": server.playit_domain if linked else None,
        "saved_tunnel_id": server.playit_tunnel_id if linked else None,
        "tunnel_created": bool(linked and server.playit_tunnel_id),
        "tunnel_create_detail": None,
    }


@router.get("/{server_id}/playit/runtime")
def get_playit_runtime_status(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)
    payload = build_payload(server, current_user)
    if server.playit_enabled and current_user.playit_agent_secret and server.status == "running" and not server.playit_tunnel_id:
        tunnel_id, domain, detail = ensure_playit_tunnel(server, current_user)
        if tunnel_id:
            server.playit_tunnel_id = tunnel_id
            server.playit_domain = domain
            db.commit()
            payload = build_payload(server, current_user)
        payload["tunnel_create_detail"] = detail
        payload["tunnel_created"] = bool(server.playit_tunnel_id)
        payload["saved_domain"] = server.playit_domain
        payload["saved_tunnel_id"] = server.playit_tunnel_id
    return payload


@router.post("/{server_id}/playit/runtime/link")
def link_playit_runtime(
    server_id: int,
    data: PlayitRuntimeLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)

    current_user.playit_agent_id = (data.agent_id or "").strip() or None
    current_user.playit_agent_secret = data.agent_secret_key.strip()
    server.playit_tunnel_id = (data.saved_tunnel_id or "").strip() or None
    server.playit_domain = (data.saved_domain or "").strip() or None
    server.playit_enabled = True
    tunnel_detail = None

    if not current_user.playit_agent_id:
        current_user.playit_agent_id = resolve_agent_id(current_user.playit_agent_secret)

    if server.status == "running":
        try:
            start_playit_container(server.id, current_user.playit_agent_secret)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to start local Playit agent: {exc}") from exc
        tunnel_id, domain, tunnel_detail = ensure_playit_tunnel(server, current_user)
        if tunnel_id:
            server.playit_tunnel_id = tunnel_id
            server.playit_domain = domain
    else:
        tunnel_detail = "Server needs to be started to make a tunnel."

    db.commit()

    payload = build_payload(server, current_user)
    payload["tunnel_create_detail"] = tunnel_detail
    payload["tunnel_created"] = bool(server.playit_tunnel_id)
    return payload


@router.post("/{server_id}/playit/runtime/sync")
def sync_playit_runtime(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)

    if not server.playit_enabled or not current_user.playit_agent_secret:
        stop_playit_container(server.id)
        return build_payload(server, current_user)

    if server.status == "running":
        try:
            start_playit_container(server.id, current_user.playit_agent_secret)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to sync local Playit agent: {exc}") from exc
        tunnel_id, domain, tunnel_detail = ensure_playit_tunnel(server, current_user)
        if tunnel_id:
            server.playit_tunnel_id = tunnel_id
            server.playit_domain = domain
        db.commit()
        payload = build_payload(server, current_user)
        payload["tunnel_create_detail"] = tunnel_detail
        payload["tunnel_created"] = bool(server.playit_tunnel_id)
        return payload
    else:
        stop_playit_container(server.id)

    return build_payload(server, current_user)


@router.post("/{server_id}/playit/runtime/disconnect")
def disconnect_playit_runtime(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_server_for_user(server_id, db, current_user)
    user_servers = db.query(Server).filter(Server.owner_id == current_user.id).all()
    for server in user_servers:
        stop_playit_container(server.id)
        server.playit_enabled = False
        server.playit_tunnel_id = None
        server.playit_domain = None

    current_user.playit_agent_id = None
    current_user.playit_agent_secret = None
    db.commit()
    return {"linked": False}
