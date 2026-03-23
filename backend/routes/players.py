import docker
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user

router = APIRouter(prefix="/api/servers/{sid}/players", tags=["players"])

@router.get("/")
def list_players(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        c = docker.from_env().containers.get(f"mc-panel-{sid}")
        if c.status != "running":
            return {"players": [], "online": 0}
        r = c.exec_run("list", stdout=True, stderr=True)
        out = r.output.decode()
        players = []
        if "online:" in out:
            parts = out.split("online:")
            if len(parts) > 1 and parts[1].strip():
                players = [p.strip() for p in parts[1].strip().split(",") if p.strip()]
        return {"players": players, "online": len(players)}
    except:
        return {"players": [], "online": 0}
