import json
import os

from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import BASE_DIR, SERVERS_DIR
from database import get_db
from models.server import Server
from models.user import User
from utils.docker_client import get_docker_client
from utils.security import decrypt_secret, encrypt_secret, get_current_user

router = APIRouter(prefix="/api/servers", tags=["sftp"])

SFTP_IMAGE = "atmoz/sftp"
SFTP_BASE_PORT = int(os.getenv("SFTP_BASE_PORT", "2223"))


def _container_name(server_id: int) -> str:
    return f"mc-panel-sftp-{server_id}"


def _state_path(server_id: int) -> str:
    return os.path.join(BASE_DIR, f"sftp_state_{server_id}.json")


def _load_state(server_id: int) -> dict:
    try:
        with open(_state_path(server_id), "r", encoding="utf-8") as f:
            state = json.load(f)
        password = state.get("password")
        if password and not str(password).startswith("gAAAA"):
            state["password"] = encrypt_secret(str(password))
            _save_state(server_id, state)
        return state
    except Exception:
        return {"enabled": False}


def _save_state(server_id: int, state: dict) -> None:
    path = _state_path(server_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _state_password(state: dict) -> str | None:
    return decrypt_secret(state.get("password"))


def _server_port(server_id: int) -> int:
    return SFTP_BASE_PORT + server_id


def _container_status(server_id: int) -> str:
    try:
        c = get_docker_client().containers.get(_container_name(server_id))
        return c.status
    except DockerNotFound:
        return "stopped"
    except Exception:
        return "unavailable"


def _stop_container(server_id: int) -> None:
    try:
        get_docker_client().containers.get(_container_name(server_id)).remove(force=True)
    except DockerNotFound:
        pass


def _get_server_dir(server_id: int) -> str | None:
    for folder in os.listdir(SERVERS_DIR):
        if folder.startswith(f"{server_id}-"):
            return os.path.join(SERVERS_DIR, folder)
    path = os.path.join(SERVERS_DIR, str(server_id))
    return path if os.path.exists(path) else None


class SftpToggleRequest(BaseModel):
    enabled: bool
    password: str | None = None


def _build_payload(server_id: int) -> dict:
    state = _load_state(server_id)
    port = _server_port(server_id)
    status = _container_status(server_id) if state.get("enabled") else "stopped"
    return {"enabled": state.get("enabled", False), "status": status, "port": port}


@router.get("/{server_id}/sftp")
def get_sftp_status(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return _build_payload(server_id)


@router.post("/{server_id}/sftp")
def toggle_sftp(
    server_id: int,
    data: SftpToggleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if not data.enabled:
        _stop_container(server_id)
        _save_state(server_id, {"enabled": False})
        return _build_payload(server_id)

    state = _load_state(server_id)
    password = data.password or _state_password(state)
    if not password:
        raise HTTPException(status_code=400, detail="Password is required to enable SFTP.")

    server_dir = _get_server_dir(server_id)
    if not server_dir:
        raise HTTPException(status_code=400, detail="Server directory not found. Start the server first.")

    _stop_container(server_id)

    try:
        get_docker_client().images.pull(SFTP_IMAGE)
    except Exception:
        pass

    port = _server_port(server_id)
    try:
        get_docker_client().containers.run(
            SFTP_IMAGE,
            command=f"panel:{password}:1000",
            name=_container_name(server_id),
            detach=True,
            ports={f"22/tcp": port},
            volumes={server_dir: {"bind": "/home/panel/files", "mode": "rw"}},
            restart_policy={"Name": "unless-stopped"},
            labels={"enderpanel.sftp": "true", "enderpanel.server_id": str(server_id)},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to start SFTP container: {exc}") from exc

    _save_state(server_id, {"enabled": True, "password": encrypt_secret(password)})
    return _build_payload(server_id)
