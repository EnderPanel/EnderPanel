import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import engine, Base
from routes import auth_router, servers_router, console_router, files_router, players_router, plugins_router, settings_router, users_router, avatars_router
from config import SERVERS_DIR, BASE_DIR

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EnderPanel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
