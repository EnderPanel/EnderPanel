import os
import re
import shutil
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user, hash_password
from utils.docker_client import get_docker_client
from config import SERVERS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    users = db.query(User).all()
    result = []
    for u in users:
        server_count = db.query(Server).filter(Server.owner_id == u.id).count()
        result.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": u.is_admin,
            "server_count": server_count
        })
    return result

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    server_count = db.query(Server).filter(Server.owner_id == user.id).count()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin,
        "server_count": server_count
    }

class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[str] = Field(default=None, min_length=5, max_length=100)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    is_admin: Optional[bool] = None

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.username:
        existing = db.query(User).filter(User.username == data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = data.username

    if data.email:
        existing = db.query(User).filter(User.email == data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = data.email

    if data.password:
        user.hashed_password = hash_password(data.password)

    if data.is_admin is not None and current_user.is_admin:
        user.is_admin = data.is_admin

    db.commit()
    return {"status": "updated", "id": user.id}

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    servers = db.query(Server).filter(Server.owner_id == user_id).all()
    try:
        docker = get_docker_client()
    except Exception:
        docker = None

    for server in servers:
        # Stop and remove Docker containers before deleting server data
        if docker:
            for container_name in (f"mc-playit-{server.id}", f"mc-panel-{server.id}"):
                try:
                    c = docker.containers.get(container_name)
                    c.remove(force=True)
                except Exception as exc:
                    logger.warning("Could not remove container %s during user deletion: %s", container_name, exc)

        server_dir = os.path.join(SERVERS_DIR, f"{server.id}-{re.sub(r'[^a-zA-Z0-9_-]', '_', server.name)}")
        if os.path.exists(server_dir):
            try:
                shutil.rmtree(server_dir)
            except Exception as exc:
                logger.warning("Could not remove server dir %s: %s", server_dir, exc)
        db.delete(server)

    db.delete(user)
    db.commit()
    return {"status": "deleted"}

@router.post("/{user_id}/make-admin")
def make_admin(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = True
    db.commit()
    return {"status": "updated", "is_admin": True}

@router.post("/{user_id}/remove-admin")
def remove_admin(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove your own admin")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_admin = False
    db.commit()
    return {"status": "updated", "is_admin": False}
