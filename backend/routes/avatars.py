import os
import re
import uuid
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import AVATARS_DIR, SERVERS_DIR

router = APIRouter(prefix="/api", tags=["avatars"])

ALLOWED_TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"]
EXTENSIONS_BY_TYPE = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
MAX_SIZE = 5 * 1024 * 1024

def sanitize_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)


def get_server_dir(server_id: int, server_name: str) -> str:
    exact_path = os.path.join(SERVERS_DIR, f"{server_id}-{sanitize_name(server_name)}")
    if os.path.isdir(exact_path):
        return exact_path

    prefix = f"{server_id}-"
    if os.path.isdir(SERVERS_DIR):
        for entry in os.listdir(SERVERS_DIR):
            if entry.startswith(prefix):
                return os.path.join(SERVERS_DIR, entry)
    return exact_path


def read_avatar_bytes(file: UploadFile) -> bytes:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only PNG, JPEG, GIF, and WebP images are allowed")

    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="Image must be under 5MB")

    try:
        with Image.open(BytesIO(content)) as img:
            img.verify()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

    return content


def save_avatar(content: bytes, content_type: str, prefix: str) -> str:
    ext = EXTENSIONS_BY_TYPE[content_type]
    filename = f"{prefix}-{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(AVATARS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(content)

    return filename


def write_server_icon(content: bytes, server: Server) -> None:
    server_dir = get_server_dir(server.id, server.name)
    if not os.path.isdir(server_dir):
        return

    try:
        with Image.open(BytesIO(content)) as img:
            fitted = ImageOps.fit(
                img.convert("RGBA"),
                (64, 64),
                Image.Resampling.LANCZOS,
            )
            temp_path = os.path.join(server_dir, "server-icon.png.tmp")
            final_path = os.path.join(server_dir, "server-icon.png")
            fitted.save(temp_path, format="PNG")
            os.replace(temp_path, final_path)
    except (UnidentifiedImageError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"Failed to create server icon: {exc}")


def remove_server_icon(server: Server) -> None:
    icon_path = os.path.join(get_server_dir(server.id, server.name), "server-icon.png")
    if os.path.exists(icon_path):
        os.remove(icon_path)

@router.post("/user/avatar")
async def upload_user_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    content = read_avatar_bytes(file)
    filename = save_avatar(content, file.content_type, f"user-{current_user.id}")
    old_avatar = current_user.avatar
    current_user.avatar = filename
    db.commit()

    if old_avatar:
        old_path = os.path.join(AVATARS_DIR, old_avatar)
        if os.path.exists(old_path):
            os.remove(old_path)

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

    content = read_avatar_bytes(file)
    filename = save_avatar(content, file.content_type, f"server-{server_id}")
    try:
        write_server_icon(content, server)
    except Exception:
        new_path = os.path.join(AVATARS_DIR, filename)
        if os.path.exists(new_path):
            os.remove(new_path)
        raise
    old_avatar = server.avatar
    server.avatar = filename
    db.commit()

    if old_avatar:
        old_path = os.path.join(AVATARS_DIR, old_avatar)
        if os.path.exists(old_path):
            os.remove(old_path)

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
    remove_server_icon(server)

    return {"status": "removed"}

@router.get("/avatars/{filename}")
def get_avatar(filename: str):
    if filename != os.path.basename(filename):
        raise HTTPException(status_code=400, detail="Invalid avatar filename")
    filepath = os.path.join(AVATARS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(filepath)
