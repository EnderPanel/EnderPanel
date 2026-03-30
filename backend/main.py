import os
import re
import html
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from database import engine, Base
from routes import auth_router, servers_router, console_router, files_router, players_router, plugins_router, settings_router, users_router, avatars_router, admin_router
from config import SERVERS_DIR, BASE_DIR

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

app = FastAPI(title="EnderPanel")
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
    blocked_dirs = (".git/", ".github/", "__pycache__/", "node_modules/", "backend/", "servers/")
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
    allow_origins=["http://localhost:8000", "http://localhost:5173", "http://127.0.0.1:8000"],
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

os.makedirs(SERVERS_DIR, exist_ok=True)

# Auto-cleanup orphaned Docker containers on startup
try:
    import docker
    from database import get_db
    from models.server import Server
    db = next(get_db())
    valid_ids = {s.id for s in db.query(Server.id).all()}
    for c in docker.from_env().containers.list(all=True):
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

DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")

if os.path.exists(DIST_DIR):
    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = os.path.join(DIST_DIR, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")
else:
    @app.get("/")
    def root():
        return {"message": "EnderPanel API", "status": "running", "note": "Frontend not built. Run 'npm run build' in frontend folder."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
