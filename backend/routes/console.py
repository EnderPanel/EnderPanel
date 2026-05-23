import asyncio
import json
import re
import socket
from contextlib import suppress

from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import ALGORITHM, SECRET_KEY
from database import SessionLocal, get_db
from models.server import Server
from models.user import User
from utils.security import AUTH_COOKIE_NAME, get_current_user
from utils.docker_client import get_docker_client


router = APIRouter(prefix="/api/servers", tags=["console"])

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
PROMPT_NOISE_RE = re.compile(r"(?m)^>\.+\s*")
PTERODACTYL_PROMPT_PREFIXES = (
    "container@pterodactyl",
)


def docker_client():
    return get_docker_client()


def container_name(server_id: int) -> str:
    return f"mc-panel-{server_id}"


def strip_console_ansi(value: str) -> str:
    return ANSI_ESCAPE_RE.sub("", value)


def clean_console_text(value: str, *, keep_ansi: bool = True) -> str:
    cleaned = value.replace("\r", "")
    cleaned = PROMPT_NOISE_RE.sub("", cleaned)
    filtered_lines: list[str] = []
    for line in cleaned.splitlines():
        detection_line = strip_console_ansi(line).strip()
        if detection_line.startswith(PTERODACTYL_PROMPT_PREFIXES):
            continue
        filtered_lines.append(line)
    cleaned = "\n".join(filtered_lines)
    if cleaned and value.endswith("\n"):
        cleaned += "\n"
    if not keep_ansi:
        cleaned = strip_console_ansi(cleaned)
    return cleaned


def encode_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=True)}\n\n"


def encode_ws(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=True)


async def get_recent_logs_text(name: str, tail: int = 100) -> str:
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "logs",
        "--tail",
        str(tail),
        name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return clean_console_text(stdout.decode("utf-8", errors="replace"), keep_ansi=True)


async def send_recent_logs(ws: WebSocket, name: str, tail: int = 100, started_at: str = "") -> None:
    text = await get_recent_logs_text(name, tail=tail)
    if text.strip():
        await ws.send_text(encode_ws({"type": "chunk", "chunk": text, "started_at": started_at}))


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


def authenticate_token(token: str | None, db: Session) -> User | None:
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


def get_auth_token_from_parts(
    cookie_token: str | None,
    authorization: str | None,
    query_token: str | None,
    *,
    allow_query_token: bool = True,
) -> str | None:
    token = cookie_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    elif allow_query_token and query_token:
        token = query_token.strip()
    return token


def authenticate_websocket(ws: WebSocket, db: Session) -> User | None:
    token = get_auth_token_from_parts(
        ws.cookies.get(AUTH_COOKIE_NAME),
        ws.headers.get("authorization"),
        ws.query_params.get("token"),
        allow_query_token=True,
    )
    return authenticate_token(token, db)


def authenticate_request(request: Request, db: Session) -> User | None:
    token = get_auth_token_from_parts(
        request.cookies.get(AUTH_COOKIE_NAME),
        request.headers.get("authorization"),
        request.query_params.get("token"),
        allow_query_token=False,
    )
    return authenticate_token(token, db)


class ConsoleCommandRequest(BaseModel):
    command: str


@router.get("/{sid}/console/recent")
async def recent_console_logs(
    sid: int,
    tail: int = Query(default=200, ge=1, le=400),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Not found")

    name = container_name(sid)
    status = "missing"
    started_at = ""
    exit_code = None

    try:
        container = get_container(name)
        container.reload()
        status = container.status
        state = container.attrs.get("State") or {}
        started_at = str(state.get("StartedAt") or "")
        exit_code = state.get("ExitCode")
    except DockerNotFound:
        pass
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Console unavailable: {exc}")

    text = ""
    if status != "missing":
        text = await get_recent_logs_text(name, tail=tail)

    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return {
        "status": status,
        "started_at": started_at,
        "exit_code": exit_code,
        "lines": lines,
    }


@router.get("/{sid}/console/stream")
async def console_stream(
    sid: int,
    request: Request,
    tail: int = Query(default=200, ge=1, le=400),
    replay: int = Query(default=1),
):
    db = SessionLocal()
    try:
        user = authenticate_request(request, db)
        if not user:
            raise HTTPException(status_code=401, detail="Could not validate credentials")

        server = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
        if not server:
            raise HTTPException(status_code=404, detail="Not found")
    finally:
        db.close()

    name = container_name(sid)

    async def event_generator():
        proc = None
        try:
            try:
                container = get_container(name)
                container.reload()
                state = container.attrs.get("State") or {}
                status = container.status
                started_at = str(state.get("StartedAt") or "")
                exit_code = state.get("ExitCode")
            except DockerNotFound:
                yield encode_sse({"type": "status", "status": "missing", "started_at": "", "exit_code": None})
                return
            except Exception as exc:
                yield encode_sse({"type": "error", "detail": f"Console unavailable: {exc}"})
                return

            yield encode_sse({
                "type": "status",
                "status": status,
                "started_at": started_at,
                "exit_code": exit_code,
            })

            if replay:
                replay_text = await get_recent_logs_text(name, tail=tail)
                for line in replay_text.splitlines():
                    clean_line = line.rstrip()
                    if clean_line:
                        yield encode_sse({"type": "line", "line": clean_line, "started_at": started_at})

            if status != "running":
                return

            proc = await asyncio.create_subprocess_exec(
                "docker",
                "logs",
                "-f",
                "--tail",
                "0",
                name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                if await request.is_disconnected():
                    break

                try:
                    raw = await asyncio.wait_for(proc.stdout.readline(), timeout=15)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                    continue

                if not raw:
                    break

                text = clean_console_text(raw.decode("utf-8", errors="replace"))
                for line in text.splitlines():
                    clean_line = line.rstrip()
                    if clean_line:
                        yield encode_sse({"type": "line", "line": clean_line, "started_at": started_at})

            with suppress(Exception):
                container = get_container(name)
                container.reload()
                state = container.attrs.get("State") or {}
                yield encode_sse({
                    "type": "status",
                    "status": container.status,
                    "started_at": str(state.get("StartedAt") or started_at),
                    "exit_code": state.get("ExitCode"),
                })
        finally:
            if proc:
                with suppress(ProcessLookupError, Exception):
                    proc.kill()
                with suppress(Exception):
                    await proc.wait()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{sid}/console/command")
async def send_console_command(
    sid: int,
    payload: ConsoleCommandRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Not found")

    command = payload.command.strip()
    if not command:
        raise HTTPException(status_code=400, detail="Command cannot be empty")

    name = container_name(sid)
    try:
        container = get_container(name)
        container.reload()
    except DockerNotFound:
        raise HTTPException(status_code=409, detail="Server not running")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Console unavailable: {exc}")

    if container.status != "running":
        raise HTTPException(status_code=409, detail=f"Server not running ({container.status})")

    attached_socket = None
    raw_socket = None
    try:
        attached_socket, raw_socket = await asyncio.to_thread(open_attach_socket, name)
        loop = asyncio.get_running_loop()
        await loop.sock_sendall(raw_socket, f"{command}\r".encode("utf-8", errors="replace"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to send command: {exc}")
    finally:
        with suppress(Exception):
            raw_socket.shutdown(socket.SHUT_RDWR)
        with suppress(Exception):
            raw_socket.close()
        with suppress(Exception):
            attached_socket.close()

    return {"ok": True}


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
        await ws.send_text(encode_ws({"type": "status", "status": "missing", "started_at": "", "exit_code": None}))
        await ws.close()
        return
    except Exception as exc:
        await ws.send_text(encode_ws({"type": "error", "detail": f"Console unavailable: {exc}"}))
        await ws.close()
        return

    container.reload()
    status = container.status
    state = container.attrs.get("State") or {}
    started_at = str(state.get("StartedAt") or "")
    exit_code = state.get("ExitCode")

    await ws.send_text(encode_ws({
        "type": "status",
        "status": status,
        "started_at": started_at,
        "exit_code": exit_code,
    }))

    if status != "running":
        if status == "exited":
            await send_recent_logs(ws, name, started_at=started_at)
        await ws.close()
        return

    client_started_at = ws.query_params.get("startedAt", "").strip()
    replay_requested = ws.query_params.get("replay", "").strip() == "1"
    if replay_requested or not client_started_at or client_started_at != started_at:
        await send_recent_logs(ws, name, started_at=started_at)

    try:
        attached_socket, raw_socket = await asyncio.to_thread(open_attach_socket, name)
    except Exception as exc:
        await ws.send_text(encode_ws({"type": "error", "detail": f"Console attach failed: {exc}"}))
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
                await ws.send_text(encode_ws({"type": "chunk", "chunk": text, "started_at": started_at}))

    output_task = asyncio.create_task(pump_output())

    try:
        while True:
            cmd = await ws.receive_text()
            command = ""
            try:
                payload = json.loads(cmd)
            except json.JSONDecodeError:
                payload = None

            if isinstance(payload, dict):
                if payload.get("event") == "send command":
                    args = payload.get("args") or []
                    if args:
                        command = str(args[0] or "")
                elif payload.get("event") == "command":
                    command = str(payload.get("command") or "")
                else:
                    command = ""
            else:
                command = cmd

            command = command.strip()
            if not command:
                continue
            payload = f"{command}\r".encode("utf-8", errors="replace")
            await loop.sock_sendall(raw_socket, payload)
    except WebSocketDisconnect:
        pass
    except (ConnectionError, OSError) as exc:
        with suppress(Exception):
            await ws.send_text(encode_ws({"type": "error", "detail": f"Console connection error: {exc}"}))
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
