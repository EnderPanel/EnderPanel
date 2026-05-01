import os
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import SERVERS_DIR

router = APIRouter(prefix="/api/servers/{server_id}/settings", tags=["settings"])

def sanitize_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def get_server_dir(server_id: int, server_name: str = None):
    if server_name:
        return os.path.join(SERVERS_DIR, f"{server_id}-{sanitize_name(server_name)}")
    for folder in os.listdir(SERVERS_DIR):
        if folder.startswith(f"{server_id}-"):
            return os.path.join(SERVERS_DIR, folder)
    return os.path.join(SERVERS_DIR, str(server_id))

@router.get("/")
def get_settings(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    props_path = os.path.join(get_server_dir(server_id, server.name), "server.properties")
    if not os.path.exists(props_path):
        return {}

    settings = {}
    with open(props_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    settings[key] = value
    return settings

class SettingsUpdate(BaseModel):
    settings: dict

@router.post("/")
def update_settings(server_id: int, data: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    props_path = os.path.join(get_server_dir(server_id, server.name), "server.properties")
    existing = {}
    if os.path.exists(props_path):
        with open(props_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        existing[key] = value

    for key, value in data.settings.items():
        if not isinstance(key, str) or not isinstance(value, (str, int, float, bool)):
            raise HTTPException(status_code=400, detail="Invalid settings key or value type")
        if "=" in key or "\n" in key or "\r" in key:
            raise HTTPException(status_code=400, detail=f"Invalid settings key: {key!r}")
        if "\n" in str(value) or "\r" in str(value):
            raise HTTPException(status_code=400, detail=f"Invalid settings value for key: {key!r}")
    existing.update(data.settings)

    with open(props_path, "w") as f:
        for key, value in existing.items():
            f.write(f"{key}={value}\n")

    if "motd" in data.settings:
        server.motd = data.settings["motd"]
    if "max-players" in data.settings:
        try:
            server.max_players = int(data.settings["max-players"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="max-players must be an integer")
    db.commit()

    return {"status": "updated", "settings": existing}
