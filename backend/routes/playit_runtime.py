import docker
import httpx
import logging
import os
import re
import secrets
import shutil
import threading
import time
from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from config import PLAYIT_AGENT_IMAGE, SERVERS_DIR, PLAYIT_SETUP_URL, PLAYIT_DASHBOARD_URL
from database import SessionLocal, get_db
from models.server import Server
from models.user import User
from utils.docker_cleanup import remove_container_if_exists
from utils.docker_client import get_docker_client
from utils.security import get_current_user


router = APIRouter(prefix="/api/servers", tags=["playit-runtime"])

PLAYIT_API_BASE = "https://api.playit.gg"
PLAYIT_CLAIM_AGENT_TYPE = "self-managed"
PLAYIT_CLAIM_VERSION = "EnderPanel"
PLAYIT_CLAIM_POLL_SECONDS = 2
PLAYIT_CLAIM_POLL_TIMEOUT_SECONDS = 600


class PlayitRuntimeLinkRequest(BaseModel):
    agent_id: str | None = Field(default=None, max_length=128)
    agent_secret_key: str = Field(min_length=1, max_length=255)
    saved_tunnel_id: str | None = Field(default=None, max_length=128)
    saved_domain: str | None = Field(default=None, max_length=255)


CLAIM_URL_RE = re.compile(r"https://playit\.gg/claim/[^\s\"']+")
SECRET_KEY_RE = re.compile(r"secret_key\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
claim_watch_threads: dict[int, threading.Thread] = {}
claim_watch_lock = threading.Lock()


def docker_client():
    return get_docker_client()


def server_container_name(server_id: int) -> str:
    return f"mc-panel-{server_id}"


def playit_container_name(server_id: int) -> str:
    return f"mc-playit-{server_id}"


def sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def server_dir(server: Server) -> str:
    return os.path.join(SERVERS_DIR, f"{server.id}-{sanitize(server.name)}")


def playit_config_dir(server: Server) -> str:
    return os.path.join(server_dir(server), ".playit")


def playit_secret_file(server: Server) -> str:
    return os.path.join(playit_config_dir(server), "playit.toml")


def playit_claim_file(server: Server) -> str:
    return os.path.join(playit_config_dir(server), "claim-code.txt")


def ensure_playit_config_dir(server: Server) -> str:
    path = playit_config_dir(server)
    os.makedirs(path, exist_ok=True)
    return path


def read_playit_secret_from_disk(server: Server) -> str | None:
    path = playit_secret_file(server)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
    except OSError:
        return None
    match = SECRET_KEY_RE.search(data)
    if not match:
        return None
    return match.group(1).strip() or None


def write_playit_secret_to_disk(server: Server, secret_key: str) -> None:
    path = playit_secret_file(server)
    ensure_playit_config_dir(server)
    tmp_path = f"{path}.tmp"
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f'secret_key = "{secret_key.strip()}"\n')
        os.replace(tmp_path, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def read_playit_claim_code(server: Server) -> str | None:
    path = playit_claim_file(server)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = f.read().strip()
    except OSError:
        return None
    return data or None


def write_playit_claim_code(server: Server, claim_code: str) -> str:
    path = playit_claim_file(server)
    ensure_playit_config_dir(server)
    with open(path, "w", encoding="utf-8") as f:
        f.write(claim_code.strip())
    return claim_code.strip()


def clear_playit_claim_code(server: Server) -> None:
    try:
        os.remove(playit_claim_file(server))
    except FileNotFoundError:
        pass
    except OSError:
        pass


def generate_playit_claim_code() -> str:
    return secrets.token_hex(5)


def build_playit_claim_url(claim_code: str | None) -> str | None:
    if not claim_code:
        return None
    return f"https://playit.gg/claim/{claim_code}"


def extract_claim_url_from_logs(log_text: str) -> str | None:
    match = CLAIM_URL_RE.search(log_text or "")
    if not match:
        return None
    return match.group(0)


def read_playit_logs(server_id: int, tail: int = 120) -> str:
    try:
        container = docker_client().containers.get(playit_container_name(server_id))
        raw = container.logs(tail=tail)
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return str(raw or "")
    except Exception:
        return ""


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
        remove_container_if_exists(playit_container_name(server_id), stop_timeout=5)
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
        with httpx.Client(timeout=20) as client:
            response = client.post(
                f"{PLAYIT_API_BASE}{path}",
                headers={
                    "Authorization": f"Agent-Key {secret_key.strip()}",
                    "Content-Type": "application/json",
                },
                json=body or {},
            )
            text = response.text
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": f"Failed to contact Playit agent API: {exc}"}
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


def call_public_api(path: str, body: dict | None = None) -> dict:
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                f"{PLAYIT_API_BASE}{path}",
                headers={"Content-Type": "application/json"},
                json=body or {},
            )
            text = response.text
    except httpx.HTTPError as exc:
        return {"ok": False, "detail": f"Failed to contact Playit public API: {exc}"}

    try:
        parsed = response.json() if text else None
    except ValueError:
        parsed = None

    if response.status_code >= 400:
        detail = None
        if isinstance(parsed, dict):
            detail = parsed.get("data") or parsed.get("error") or parsed.get("message")
        return {
            "ok": False,
            "detail": str(detail or f"Playit public API request failed with status {response.status_code}."),
            "parsed": parsed,
        }

    if not isinstance(parsed, dict):
        return {"ok": False, "detail": "Playit public API returned invalid JSON.", "parsed": parsed}

    status = parsed.get("status")
    if status == "success":
        return {"ok": True, "data": parsed.get("data"), "parsed": parsed}

    detail = parsed.get("data") or parsed.get("error") or parsed.get("message")
    return {
        "ok": False,
        "detail": str(detail or "Playit public API returned a failure status."),
        "parsed": parsed,
    }


def claim_status_message(status: str | None) -> str | None:
    return {
        "WaitingForUserVisit": "Open the claim link to start linking this Playit agent.",
        "WaitingForUser": "Approve this Playit agent in your browser to finish linking.",
        "UserAccepted": "Playit claim approved. Finishing setup...",
        "UserRejected": "Playit claim was rejected in the browser.",
    }.get(str(status or ""))


def ensure_playit_claim(server: Server) -> tuple[str | None, str | None, str | None, str | None]:
    stale_errors = {"InvalidCode", "CodeExpired", "CodeNotFound"}

    for _ in range(2):
        claim_code = read_playit_claim_code(server)
        if not claim_code:
            claim_code = write_playit_claim_code(server, generate_playit_claim_code())

        claim_url = build_playit_claim_url(claim_code)
        setup = call_public_api(
            "/claim/setup",
            {
                "code": claim_code,
                "agent_type": PLAYIT_CLAIM_AGENT_TYPE,
                "version": PLAYIT_CLAIM_VERSION,
            },
        )

        if setup.get("ok"):
            status = str(setup.get("data") or "")
            return claim_code, claim_url, status, claim_status_message(status)

        detail = str(setup.get("detail") or "")
        if detail in stale_errors:
            clear_playit_claim_code(server)
            continue
        return claim_code, claim_url, None, detail or "Could not prepare a Playit claim link."

    claim_code = write_playit_claim_code(server, generate_playit_claim_code())
    return claim_code, build_playit_claim_url(claim_code), None, "Generated a new Playit claim link."


def resolve_playit_secret(server: Server) -> tuple[str | None, str | None, str | None]:
    secret = read_playit_secret_from_disk(server)
    if secret:
        return secret, None, None

    claim_code, claim_url, claim_status, claim_detail = ensure_playit_claim(server)
    if not claim_code:
        return None, None, claim_detail or "Could not start the Playit claim flow."

    if claim_status == "UserRejected":
        clear_playit_claim_code(server)
        return None, None, "Playit claim was rejected. Refresh to get a new claim link."

    if claim_status != "UserAccepted":
        return None, claim_url, claim_detail or "Open the Playit claim link and approve the agent."

    exchange = call_public_api("/claim/exchange", {"code": claim_code})
    if exchange.get("ok"):
        data = exchange.get("data") or {}
        if isinstance(data, dict):
            secret_key = str(data.get("secret_key") or "").strip()
            if secret_key:
                write_playit_secret_to_disk(server, secret_key)
                clear_playit_claim_code(server)
                return secret_key, None, "Playit claim complete."
        return None, claim_url, "Playit returned an invalid secret response."

    detail = str(exchange.get("detail") or "")
    if detail in {"CodeExpired", "CodeNotFound"}:
        clear_playit_claim_code(server)
        _, new_claim_url, _, new_claim_detail = ensure_playit_claim(server)
        return None, new_claim_url, new_claim_detail or "The old claim link expired. A new one has been created."
    if detail == "UserRejected":
        clear_playit_claim_code(server)
        return None, None, "Playit claim was rejected. Refresh to get a new claim link."
    if detail in {"NotAccepted", "NotSetup"}:
        return None, claim_url, claim_detail or "Open the Playit claim link and approve the agent."

    return None, claim_url, detail or claim_detail or "Could not finish the Playit claim flow."


def run_playit_claim_watcher(server_id: int) -> None:
    started_at = time.time()
    try:
        while time.time() - started_at < PLAYIT_CLAIM_POLL_TIMEOUT_SECONDS:
            db = SessionLocal()
            try:
                server = db.query(Server).filter(Server.id == server_id).first()
                if not server or not server.playit_enabled:
                    return

                secret = read_playit_secret_from_disk(server)
                if not secret:
                    secret, _, _ = resolve_playit_secret(server)

                if not secret:
                    time.sleep(PLAYIT_CLAIM_POLL_SECONDS)
                    continue

                if server.status == "running":
                    try:
                        start_playit_container(server)
                        tunnel_id, domain, _ = ensure_playit_tunnel(server, secret)
                        if tunnel_id:
                            server.playit_tunnel_id = tunnel_id
                            server.playit_domain = domain
                            db.commit()
                    except Exception:
                        logger.exception("Failed to finish Playit claim watcher for server %s", server_id)
                return
            finally:
                db.close()

            time.sleep(PLAYIT_CLAIM_POLL_SECONDS)
    finally:
        with claim_watch_lock:
            claim_watch_threads.pop(server_id, None)


def spawn_playit_claim_watcher(server_id: int) -> None:
    with claim_watch_lock:
        existing = claim_watch_threads.get(server_id)
        if existing and existing.is_alive():
            return
        worker = threading.Thread(
            target=run_playit_claim_watcher,
            args=(server_id,),
            name=f"playit-claim-{server_id}",
            daemon=True,
        )
        claim_watch_threads[server_id] = worker
        worker.start()


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


def ensure_playit_tunnel(server: Server, secret_key: str) -> tuple[str | None, str | None, str | None]:
    if not secret_key:
        return server.playit_tunnel_id, server.playit_domain, "Missing Playit agent secret."

    resolved_agent_id = resolve_agent_id(secret_key, None)
    if not resolved_agent_id:
        return server.playit_tunnel_id, server.playit_domain, "Playit agent is not ready yet."

    if server.playit_tunnel_id:
        run_data_v1 = call_agent_api(secret_key, "/v1/agents/rundata", {})
        if run_data_v1.get("ok"):
            tunnel = find_matching_tunnel((run_data_v1.get("data") or {}).get("tunnels"), server.playit_tunnel_id, server.port)
            domain = pick_tunnel_address(tunnel)
            if domain:
                return server.playit_tunnel_id, domain, None
        return server.playit_tunnel_id, server.playit_domain, None

    legacy_create = call_agent_api(
        secret_key,
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
            secret_key,
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
        run_data = call_agent_api(secret_key, path, {})
        if run_data.get("ok"):
            tunnels = (run_data.get("data") or {}).get("tunnels") or []
            tunnel = find_matching_tunnel(tunnels, tunnel_id, server.port)
            logger.warning("playit rundata path=%s tunnel_id=%s tunnel=%s", path, tunnel_id, tunnel)
            domain = pick_tunnel_address(tunnel)
            if domain:
                break

    return tunnel_id, domain or None, None


def start_playit_container(server: Server) -> None:
    if not read_playit_secret_from_disk(server):
        raise RuntimeError("Playit is not claimed yet")

    client = docker_client()
    server_container = client.containers.get(server_container_name(server.id))
    server_container.reload()
    if server_container.status != "running":
        raise RuntimeError("Server must be running before Playit can attach")

    stop_playit_container(server.id)
    config_dir = ensure_playit_config_dir(server)

    client.containers.run(
        PLAYIT_AGENT_IMAGE,
        name=playit_container_name(server.id),
        detach=True,
        network_mode=f"container:{server_container_name(server.id)}",
        restart_policy={"Name": "unless-stopped"},
        entrypoint=["/usr/local/bin/playit"],
        command=["-s", "--secret_path", "/etc/playit/playit.toml", "--platform_docker", "start"],
        volumes={config_dir: {"bind": "/etc/playit", "mode": "rw"}},
        labels={"enderpanel.playit": "true", "enderpanel.server_id": str(server.id)},
    )


def build_payload(server: Server) -> dict:
    secret = read_playit_secret_from_disk(server)
    claim_code = read_playit_claim_code(server)
    claim_url = build_playit_claim_url(claim_code) if not secret else None
    linked = bool(server.playit_enabled and secret)
    return {
        "linked": linked,
        "enabled": bool(server.playit_enabled),
        "server_running": server.status == "running",
        "agent_running": playit_container_running(server.id),
        "agent_id": None,
        "agent_secret_masked": mask_secret(secret) if linked else None,
        "saved_domain": server.playit_domain if linked else None,
        "saved_tunnel_id": server.playit_tunnel_id if linked else None,
        "tunnel_created": bool(linked and server.playit_tunnel_id),
        "tunnel_create_detail": None,
        "claim_url": claim_url,
        "setup_url": PLAYIT_SETUP_URL,
        "dashboard_url": PLAYIT_DASHBOARD_URL,
        "log_hint": None,
    }


def refresh_playit_tunnel_state(server: Server) -> tuple[str | None, str | None, str | None]:
    secret = read_playit_secret_from_disk(server)
    if not server.playit_enabled or not secret:
        return server.playit_tunnel_id, server.playit_domain, None

    # If a tunnel already exists, we can refresh its public hostname from Playit
    # even when the local sidecar is stopped. Creating a missing tunnel still
    # requires the server to be running.
    if server.playit_tunnel_id or server.status == "running":
        return ensure_playit_tunnel(server, secret)

    return server.playit_tunnel_id, server.playit_domain, "Server needs to be started to make a tunnel."


@router.get("/{server_id}/playit/runtime")
def get_playit_runtime_status(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)
    payload = build_payload(server)
    if server.playit_enabled and read_playit_secret_from_disk(server):
        tunnel_id, domain, detail = refresh_playit_tunnel_state(server)
        if tunnel_id:
            server.playit_tunnel_id = tunnel_id
            server.playit_domain = domain
            db.commit()
            payload = build_payload(server)
        payload["tunnel_create_detail"] = detail
        payload["tunnel_created"] = bool(server.playit_tunnel_id)
        payload["saved_domain"] = server.playit_domain
        payload["saved_tunnel_id"] = server.playit_tunnel_id
    elif server.playit_enabled:
        _, claim_url, _, claim_detail = ensure_playit_claim(server)
        spawn_playit_claim_watcher(server.id)
        payload = build_payload(server)
        payload["claim_url"] = claim_url or payload.get("claim_url")
        payload["tunnel_create_detail"] = claim_detail
    return payload


@router.post("/{server_id}/playit/runtime/enable")
def enable_playit_runtime(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)
    server.playit_enabled = True
    db.commit()

    secret = read_playit_secret_from_disk(server)
    claim_url = None
    claim_detail = None
    tunnel_detail = None

    if not secret:
        secret, claim_url, claim_detail = resolve_playit_secret(server)
        if not secret:
            spawn_playit_claim_watcher(server.id)

    if server.status == "running":
        if secret:
            try:
                start_playit_container(server)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to start local Playit agent: {exc}") from exc

            tunnel_id, domain, tunnel_detail = ensure_playit_tunnel(server, secret)
            if tunnel_id:
                server.playit_tunnel_id = tunnel_id
                server.playit_domain = domain
                db.commit()
        else:
            stop_playit_container(server.id)

    payload = build_payload(server)
    payload["claim_url"] = claim_url or payload.get("claim_url")
    payload["tunnel_create_detail"] = tunnel_detail or claim_detail or payload.get("log_hint")
    payload["tunnel_created"] = bool(server.playit_tunnel_id)
    return payload


@router.post("/{server_id}/playit/runtime/link")
def link_playit_runtime(
    server_id: int,
    data: PlayitRuntimeLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raise HTTPException(status_code=410, detail="The old Playit setup-code flow was removed. Use enable/sync and claim the agent directly from the Playit page.")


@router.post("/{server_id}/playit/runtime/sync")
def sync_playit_runtime(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)

    secret = read_playit_secret_from_disk(server)
    claim_url = None
    claim_detail = None

    if not server.playit_enabled:
        stop_playit_container(server.id)
        return build_payload(server)

    if not secret:
        secret, claim_url, claim_detail = resolve_playit_secret(server)
        if not secret:
            spawn_playit_claim_watcher(server.id)

    if server.status == "running":
        if secret:
            try:
                start_playit_container(server)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Failed to sync local Playit agent: {exc}") from exc
        else:
            stop_playit_container(server.id)
    else:
        stop_playit_container(server.id)

    tunnel_id = domain = tunnel_detail = None
    if secret:
        tunnel_id, domain, tunnel_detail = refresh_playit_tunnel_state(server)
    if tunnel_id:
        server.playit_tunnel_id = tunnel_id
        server.playit_domain = domain
    db.commit()
    payload = build_payload(server)
    payload["claim_url"] = claim_url or payload.get("claim_url")
    payload["tunnel_create_detail"] = tunnel_detail or claim_detail or payload.get("log_hint")
    payload["tunnel_created"] = bool(server.playit_tunnel_id)
    return payload


@router.post("/{server_id}/playit/runtime/disconnect")
def disconnect_playit_runtime(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, db, current_user)
    stop_playit_container(server.id)
    server.playit_enabled = False
    server.playit_tunnel_id = None
    server.playit_domain = None
    try:
        shutil.rmtree(playit_config_dir(server), ignore_errors=True)
    except Exception:
        pass
    db.commit()
    return {"linked": False}
