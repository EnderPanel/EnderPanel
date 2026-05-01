import os
import re
import html
import shutil
import socket
import subprocess
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
        if os.path.exists(FRONTEND_DIR):
            start_frontend_dev_server(FRONTEND_DIR, 3000)
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

# Auto-cleanup orphaned Docker containers on startup
try:
    from database import get_db
    from models.server import Server
    from utils.docker_client import get_docker_client
    db = next(get_db())
    valid_ids = {s.id for s in db.query(Server.id).all()}
    for c in get_docker_client().containers.list(all=True):
        if c.name.startswith("mc-panel-"):
            try:
                cid = int(c.name.replace("mc-panel-", ""))
                if cid not in valid_ids:
                    c.kill()
                    c.remove(force=True)
                    print(f"Cleaned up orphaned container: {c.name}")
            except:
                pass
    db.close()
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


def start_frontend_dev_server(frontend_dir: str, port: int = 3000) -> None:
    if not os.path.exists(frontend_dir):
        print(f"Frontend directory not found: {frontend_dir}")
        return

    if not shutil.which("npm"):
        print("npm not found: frontend dev server will not be started automatically.")
        return

    if not is_port_available(port):
        print(f"Port {port} is already in use; frontend dev server will not be started.")
        return

    npm_cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(port)]
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


if __name__ == "__main__":
    if not os.path.exists(DIST_DIR) and os.path.exists(FRONTEND_DIR):
        start_frontend_dev_server(FRONTEND_DIR, 3000)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
