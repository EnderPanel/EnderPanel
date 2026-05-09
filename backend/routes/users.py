from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from fastapi import Response
from database import get_db
from models.user import User
from models.server import Server
from utils.security import create_access_token, get_current_user, hash_password, set_auth_cookie
from .servers import cleanup_server_runtime_artifacts, remove_server_dir

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
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None

@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    if current_user.id == user.id and data.username:
        token = create_access_token({"sub": user.username})
        set_auth_cookie(response, token)
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
    for server in servers:
        cleanup_server_runtime_artifacts(server.id)
        from config import SERVERS_DIR
        import os
        import re

        server_dir = os.path.join(SERVERS_DIR, f"{server.id}-{re.sub(r'[^a-zA-Z0-9_-]', '_', server.name)}")
        remove_server_dir(server_dir)
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
