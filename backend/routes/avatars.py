import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import AVATARS_DIR

router = APIRouter(prefix="/api", tags=["avatars"])

ALLOWED_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"]
MAX_SIZE = 5 * 1024 * 1024

def save_avatar(file: UploadFile, prefix: str) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG, JPEG, GIF, and WebP images are allowed")

    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{prefix}-{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(AVATARS_DIR, filename)

    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Image must be under 5MB")

    with open(filepath, "wb") as f:
        f.write(content)

    return filename

@router.post("/user/avatar")
async def upload_user_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.avatar:
        old_path = os.path.join(AVATARS_DIR, current_user.avatar)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = save_avatar(file, f"user-{current_user.id}")
    current_user.avatar = filename
    db.commit()

    return {"avatar": filename, "url": f"/api/avatars/{filename}"}

@router.delete("/user/avatar")
def delete_user_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.avatar:
        old_path = os.path.join(AVATARS_DIR, current_user.avatar)
        if os.path.exists(old_path):
            os.remove(old_path)
        current_user.avatar = None
        db.commit()

    return {"status": "removed"}

@router.post("/servers/{server_id}/avatar")
async def upload_server_avatar(
    server_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if server.avatar:
        old_path = os.path.join(AVATARS_DIR, server.avatar)
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = save_avatar(file, f"server-{server_id}")
    server.avatar = filename
    db.commit()

    return {"avatar": filename, "url": f"/api/avatars/{filename}"}

@router.delete("/servers/{server_id}/avatar")
def delete_server_avatar(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if server.avatar:
        old_path = os.path.join(AVATARS_DIR, server.avatar)
        if os.path.exists(old_path):
            os.remove(old_path)
        server.avatar = None
        db.commit()

    return {"status": "removed"}

@router.get("/avatars/{filename}")
def get_avatar(filename: str):
    filepath = os.path.join(AVATARS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(filepath)
