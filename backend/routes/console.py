import asyncio
import re
import socket
from contextlib import suppress

from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import ALGORITHM, SECRET_KEY
from database import SessionLocal
from models.server import Server
from models.user import User
from utils.security import AUTH_COOKIE_NAME
from utils.docker_client import get_docker_client


router = APIRouter(prefix="/api/servers", tags=["console"])

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
PROMPT_NOISE_RE = re.compile(r"(?m)^>\.+\s*")


def docker_client():
    return get_docker_client()


def container_name(server_id: int) -> str:
    return f"mc-panel-{server_id}"


def clean_console_text(value: str) -> str:
    cleaned = ANSI_ESCAPE_RE.sub("", value).replace("\r", "")
    cleaned = PROMPT_NOISE_RE.sub("", cleaned)
    return cleaned


async def send_recent_logs(ws: WebSocket, name: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "logs",
        "--tail",
        "100",
        name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    text = clean_console_text(stdout.decode("utf-8", errors="replace"))
    if text.strip():
        await ws.send_text(text)


def get_container(name: str):
    return docker_client().containers.get(name)


def get_started_at(name: str) -> str:
    try:
        container = get_container(name)
        return str((container.attrs.get("State") or {}).get("StartedAt") or "")
    except Exception:
        return ""


def open_attach_socket(name: str):
    client = docker_client()
    container = client.containers.get(name)
    sock = client.api.attach_socket(
        container.id,
        params={
            "stdin": 1,
            "stdout": 1,
            "stderr": 1,
            "stream": 1,
            "logs": 0,
        },
        ws=False,
    )
    raw = sock._sock if hasattr(sock, "_sock") else sock
    raw.setblocking(False)
    return sock, raw


def authenticate_websocket(ws: WebSocket, db: Session) -> User | None:
    token = ws.cookies.get(AUTH_COOKIE_NAME)
    authorization = ws.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    username = payload.get("sub")
    if not username:
        return None

    return db.query(User).filter(User.username == username).first()


@router.websocket("/{sid}/ws")
async def console(ws: WebSocket, sid: int):
    name = container_name(sid)

    db = SessionLocal()
    try:
        user = authenticate_websocket(ws, db)
        if not user:
            await ws.close(code=1008)
            return

        server = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
        if not server:
            await ws.close(code=1008)
            return
    finally:
        db.close()

    await ws.accept()

    try:
        container = get_container(name)
    except DockerNotFound:
        await ws.send_text("Server not running (missing)")
        await ws.close()
        return
    except Exception as exc:
        await ws.send_text(f"Console unavailable: {exc}")
        await ws.close()
        return

    container.reload()
    status = container.status
    if status != "running":
        if status == "exited":
            await send_recent_logs(ws, name)
        await ws.send_text(f"Server not running ({status})")
        await ws.close()
        return

    started_at = get_started_at(name)
    client_started_at = ws.query_params.get("startedAt", "").strip()
    replay_requested = ws.query_params.get("replay", "").strip() == "1"
    if replay_requested or not client_started_at or client_started_at != started_at:
        await send_recent_logs(ws, name)

    try:
        attached_socket, raw_socket = await asyncio.to_thread(open_attach_socket, name)
    except Exception as exc:
        await ws.send_text(f"Console attach failed: {exc}")
        await ws.close()
        return

    loop = asyncio.get_running_loop()

    async def pump_output():
        while True:
            chunk = await loop.sock_recv(raw_socket, 4096)
            if not chunk:
                break
            text = clean_console_text(chunk.decode("utf-8", errors="replace"))
            if text:
                await ws.send_text(text)

    output_task = asyncio.create_task(pump_output())

    try:
        while True:
            cmd = await ws.receive_text()
            command = cmd.strip()
            if not command:
                continue
            payload = f"{command}\r".encode("utf-8", errors="replace")
            await loop.sock_sendall(raw_socket, payload)
    except WebSocketDisconnect:
        pass
    except (ConnectionError, OSError) as exc:
        with suppress(Exception):
            await ws.send_text(f"Console connection error: {exc}")
    finally:
        output_task.cancel()
        with suppress(asyncio.CancelledError, Exception):
            await output_task
        with suppress(Exception):
            raw_socket.shutdown(socket.SHUT_RDWR)
        with suppress(Exception):
            raw_socket.close()
        with suppress(Exception):
            attached_socket.close()
