import os
import re
import html
import shutil
import socket
import subprocess
import signal
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import engine, Base, SessionLocal
from routes import auth_router, servers_router, console_router, files_router, players_router, plugins_router, settings_router, users_router, avatars_router, admin_router, update_router, playit_runtime_router, server_network_router, sftp_router
from config import SERVERS_DIR, BASE_DIR
from utils.docker_client import close_docker_client, get_docker_client
from utils.docker_cleanup import remove_container_if_exists
from utils.http_compat import patch_http_response_close

patch_http_response_close()

Base.metadata.create_all(bind=engine)

def run_migrations():
    """Add missing columns to existing tables (safe to run on every startup)."""
    migrations = [
        ("servers", "swap_mb", "INTEGER NOT NULL DEFAULT 512"),
        ("users", "totp_secret", "VARCHAR(32) NULL"),
        ("servers", "playit_enabled", "INTEGER NOT NULL DEFAULT 0"),
        ("users", "playit_api_key", "VARCHAR(255) NULL"),
        ("servers", "playit_tunnel_id", "VARCHAR(128) NULL"),
        ("servers", "playit_domain", "VARCHAR(255) NULL"),
        ("users", "playit_claim_id", "VARCHAR(64) NULL"),
        ("users", "playit_agent_id", "VARCHAR(128) NULL"),
        ("users", "playit_agent_secret", "VARCHAR(255) NULL"),
    ]
    with engine.connect() as conn:
        for table, column, definition in migrations:
            rows = conn.execute(
                __import__("sqlalchemy").text(f"PRAGMA table_info({table})")
            ).fetchall()
            existing = {row[1] for row in rows}
            if column not in existing:
                conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                    )
                )
                conn.commit()
                print(f"Migration: added column '{column}' to '{table}'")

run_migrations()


def run_security_backfills():
    db = SessionLocal()
    try:
        from models.user import User

        users = db.query(User).all()
        changed = False
        for user in users:
            raw_secret = getattr(user, "_playit_agent_secret", None)
            if raw_secret and not raw_secret.startswith("gAAAA"):
                user.playit_agent_secret = raw_secret
                changed = True

        if changed:
            db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Security backfill skipped: {exc}")
    finally:
        db.close()


run_security_backfills()


limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
BRANDING_DIR = os.path.join(BASE_DIR, "branding")
DIST_INDEX = os.path.join(DIST_DIR, "index.html")


def stop_managed_containers_on_shutdown() -> None:
    try:
        client = get_docker_client()
    except Exception as exc:
        print(f"Shutdown cleanup skipped: could not get Docker client: {exc}")
        return

    db = SessionLocal()
    try:
        from models.server import Server

        servers = db.query(Server).all()
        for server in servers:
            for container_name in (f"mc-playit-{server.id}", f"mc-panel-{server.id}"):
                try:
                    container = client.containers.get(container_name)
                except Exception:
                    continue

                try:
                    if container.status == "running":
                        container.stop(timeout=30)
                except Exception as exc:
                    print(f"Failed to stop container {container_name} during shutdown: {exc}")

            server.status = "stopped"

        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Shutdown cleanup failed: {exc}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        if should_start_frontend_dev_server():
            start_frontend_dev_server(FRONTEND_DIR, 3000)
        elif os.path.exists(DIST_INDEX):
            print("Using built frontend from frontend/dist; open http://localhost:8000")
    except Exception as e:
        print(f"Warning: Failed to start frontend dev server: {e}")
    try:
        yield
    finally:
        stop_managed_containers_on_shutdown()
        close_docker_client()

app = FastAPI(title="EnderPanel", lifespan=lifespan)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Slow down."})

INJECTION_PATTERNS = [
    re.compile(r"(--|;|/\*|\*/|xp_|union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+.*set)", re.IGNORECASE),
    re.compile(r"(<script|javascript:|on\w+\s*=)", re.IGNORECASE),
    re.compile(r"(\.\./|\.\.\\)", re.IGNORECASE),
]

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    path = request.url.path

    # Block sensitive files
    blocked_extensions = (".env", ".git", ".gitignore", ".py", ".pyc", ".db", ".sqlite", ".log", ".sh", ".ps1", ".json")
    blocked_dirs = ("__pycache__", "node_modules", "backend/", "servers/", ".git/")

    if not path.startswith("/api/"):
        if any(path.endswith(ext) for ext in blocked_extensions) or any(d in path for d in blocked_dirs):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

    # Check query params and path for injection patterns
    if not path.startswith("/api/"):
        check = f"{path}?{request.url.query}" if request.url.query else path
        for pattern in INJECTION_PATTERNS:
            if pattern.search(check):
                return JSONResponse(status_code=400, content={"detail": "Blocked: suspicious input detected"})

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:8000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-EnderPanel-Token"],
)

app.include_router(auth_router)
app.include_router(servers_router)
app.include_router(console_router)
app.include_router(files_router)
app.include_router(players_router)
app.include_router(plugins_router)
app.include_router(settings_router)
app.include_router(users_router)
app.include_router(avatars_router)
app.include_router(admin_router)
app.include_router(update_router)
app.include_router(playit_runtime_router)
app.include_router(server_network_router)
app.include_router(sftp_router)

os.makedirs(SERVERS_DIR, exist_ok=True)
os.makedirs(BRANDING_DIR, exist_ok=True)
app.mount("/branding", StaticFiles(directory=BRANDING_DIR), name="branding")

MANAGED_CONTAINER_PREFIXES = (
    "mc-panel-",
    "mc-playit-",
    "mc-panel-sftp-",
    "mc-panel-helper-",
)


def _extract_managed_server_id(container_name: str) -> int | None:
    for prefix in MANAGED_CONTAINER_PREFIXES:
        if container_name.startswith(prefix):
            suffix = container_name[len(prefix):]
            try:
                return int(suffix)
            except ValueError:
                return None
    return None


def _is_helper_container(container_name: str) -> bool:
    return container_name.startswith("mc-panel-helper-")


def cleanup_orphaned_managed_containers_on_startup() -> None:
    from models.server import Server
    from routes.sftp import cleanup_sftp_server_artifacts

    db = SessionLocal()
    try:
        valid_ids = {row.id for row in db.query(Server.id).all()}
        client = get_docker_client()
        for container in client.containers.list(all=True):
            container_name = container.name
            if _is_helper_container(container_name):
                try:
                    remove_container_if_exists(container_name, stop_timeout=5)
                    print(f"Cleaned up orphaned helper container: {container_name}")
                except Exception as exc:
                    print(f"Failed to clean up orphaned helper container {container_name}: {exc}")
                continue

            server_id = _extract_managed_server_id(container_name)
            if server_id is None or server_id in valid_ids:
                continue

            try:
                if container_name.startswith("mc-panel-sftp-"):
                    cleanup_sftp_server_artifacts(server_id)
                else:
                    remove_container_if_exists(container_name, stop_timeout=5)
                print(f"Cleaned up orphaned container: {container_name}")
            except Exception as exc:
                print(f"Failed to clean up orphaned container {container_name}: {exc}")

        for entry in os.listdir(BASE_DIR):
            match = re.fullmatch(r"sftp_state_(\d+)\.json", entry)
            if not match:
                continue
            server_id = int(match.group(1))
            if server_id in valid_ids:
                continue
            try:
                cleanup_sftp_server_artifacts(server_id)
                print(f"Removed orphaned SFTP state: {entry}")
            except Exception as exc:
                print(f"Failed to remove orphaned SFTP state {entry}: {exc}")
    finally:
        db.close()


try:
    cleanup_orphaned_managed_containers_on_startup()
except Exception as e:
    print(f"Container cleanup skipped: {e}")



if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = os.path.join(DIST_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "message": "EnderPanel API",
            "status": "running",
            "note": "Frontend not built. Run 'npm run dev' in frontend folder to start the dev server on http://localhost:3000."
        }


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _find_port_processes(port: int) -> list[int]:
    commands: list[list[str]] = []
    if os.name == "nt":
        commands.append(["netstat", "-ano"])
    else:
        commands.extend([
            ["lsof", "-ti", f"tcp:{port}"],
            ["lsof", "-ti", f":{port}"],
        ])

    for command in commands:
        if not shutil.which(command[0]):
            continue
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except Exception:
            continue

        if os.name == "nt":
            pids = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if f":{port}" not in line:
                    continue
                parts = line.split()
                if len(parts) >= 5 and parts[0].upper() == "TCP" and parts[3].upper() == "LISTENING":
                    try:
                        pids.append(int(parts[-1]))
                    except ValueError:
                        continue
            if pids:
                return sorted(set(pids))
            continue

        pids = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                pids.append(int(line))
            except ValueError:
                continue
        if pids:
            return sorted(set(pids))

    return []


def _kill_processes_using_port(port: int) -> bool:
    pids = _find_port_processes(port)
    if not pids:
        return False

    if os.name == "nt":
        for pid in pids:
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        time.sleep(1)
        return is_port_available(port)

    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            continue

    for _ in range(20):
        if is_port_available(port):
            return True
        time.sleep(0.1)

    for pid in pids:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            continue

    for _ in range(20):
        if is_port_available(port):
            return True
        time.sleep(0.1)

    return is_port_available(port)


def _confirm_kill_port_process(port: int) -> bool:
    pids = _find_port_processes(port)
    if not pids:
        return False

    if not os.isatty(0):
        print(f"Port {port} is already in use by PID(s): {', '.join(str(pid) for pid in pids)}; frontend dev server will not be started.")
        return False

    answer = input(
        f"Port {port} is already in use by PID(s): {', '.join(str(pid) for pid in pids)}. "
        f"Kill the process{'es' if len(pids) != 1 else ''} using port {port}? [y/N]: "
    ).strip().lower()
    if answer not in {"y", "yes"}:
        print(f"Keeping existing process on port {port}; frontend dev server will not be started.")
        return False

    if not _kill_processes_using_port(port):
        print(f"Failed to free port {port}; frontend dev server will not be started.")
        return False

    print(f"Freed port {port}; starting frontend dev server.")
    return True


def start_frontend_dev_server(frontend_dir: str, port: int = 3000) -> None:
    if not os.path.exists(frontend_dir):
        print(f"Frontend directory not found: {frontend_dir}")
        return

    npm_executable = shutil.which("npm.cmd") if os.name == "nt" else None
    if not npm_executable:
        npm_executable = shutil.which("npm")

    if not npm_executable:
        print("npm not found: frontend dev server will not be started automatically.")
        return

    package_json = os.path.join(frontend_dir, "package.json")
    if not os.path.exists(package_json):
        print(f"package.json not found in frontend directory: {frontend_dir}")
        return

    if not is_port_available(port):
        if port == 3000 and not _confirm_kill_port_process(port):
            return
        if not is_port_available(port):
            print(f"Port {port} is already in use; frontend dev server will not be started.")
            return

    npm_cmd = [npm_executable, "run", "dev", "--", "--host", "0.0.0.0", "--port", str(port)]
    popen_kwargs = {}
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True
    elif os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    try:
        print(f"Starting frontend dev server on port {port}...")
        subprocess.Popen(
            npm_cmd,
            cwd=frontend_dir,
            env=os.environ.copy(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            **popen_kwargs,
        )
        print(f"Started frontend dev server; open http://localhost:{port} or http://<this-machine-ip>:{port}")
    except Exception as exc:
        print(f"Failed to start frontend dev server: {exc}")


def should_start_frontend_dev_server() -> bool:
    env_force = os.getenv("ENDERPANEL_START_FRONTEND_DEV", "").strip().lower()
    if env_force in {"1", "true", "yes", "on"}:
        return True

    env_disable = os.getenv("ENDERPANEL_DISABLE_FRONTEND_DEV", "").strip().lower()
    if env_disable in {"1", "true", "yes", "on"}:
        return False

    if os.name == "nt":
        return False

    if os.path.exists(DIST_INDEX):
        return False

    return (
        os.path.exists(FRONTEND_DIR)
        and os.path.exists(os.path.join(FRONTEND_DIR, "package.json"))
        and os.path.exists(os.path.join(FRONTEND_DIR, "src"))
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
