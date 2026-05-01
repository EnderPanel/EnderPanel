from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.server import Server
from utils.docker_client import get_docker_client
from utils.minecraft_status import query_minecraft_status
from utils.security import get_current_user

router = APIRouter(prefix="/api/servers/{sid}/players", tags=["players"])

@router.get("/")
def list_players(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        c = get_docker_client().containers.get(f"mc-panel-{sid}")
        if c.status != "running":
            return {"players": [], "online": 0}
        status = query_minecraft_status("127.0.0.1", int(s.port))
        players_info = status.get("players") or {}
        sample = players_info.get("sample") or []
        players = [player.get("name") for player in sample if isinstance(player, dict) and player.get("name")]
        online = int(players_info.get("online") or 0)
        return {"players": players, "online": online}
    except Exception:
        return {"players": [], "online": 0}
