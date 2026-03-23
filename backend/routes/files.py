import os
import shutil
import zipfile
import time
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import SERVERS_DIR

router = APIRouter(prefix="/api/servers/{server_id}/files", tags=["files"])

def sanitize_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def get_server_dir(server_id: int, server_name: str = None):
    if server_name:
        return os.path.join(SERVERS_DIR, f"{server_id}-{sanitize_name(server_name)}")
    for folder in os.listdir(SERVERS_DIR):
        if folder.startswith(f"{server_id}-"):
            return os.path.join(SERVERS_DIR, folder)
    return os.path.join(SERVERS_DIR, str(server_id))

def safe_path(server_id: int, path: str, server_name: str = None) -> str:
    full_path = os.path.normpath(os.path.join(get_server_dir(server_id, server_name), path))
    server_dir = os.path.normpath(get_server_dir(server_id, server_name))
    if not full_path.startswith(server_dir):
        raise HTTPException(status_code=400, detail="Invalid path")
    return full_path

@router.get("/")
def list_files(server_id: int, path: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    dir_path = safe_path(server_id, path, server.name)
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="Path not found")

    items = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        items.append({
            "name": item,
            "is_dir": os.path.isdir(item_path),
            "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
            "modified": os.path.getmtime(item_path)
        })
    return items

@router.get("/read")
def read_file(server_id: int, path: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    file_path = safe_path(server_id, path, server.name)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return {"content": content, "path": path}

class FileWrite(BaseModel):
    path: str
    content: str

@router.post("/write")
def write_file(server_id: int, file: FileWrite, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    file_path = safe_path(server_id, file.path, server.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(file.content)
    return {"status": "saved", "path": file.path}

@router.post("/upload")
async def upload_file(server_id: int, path: str = "", file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    upload_dir = safe_path(server_id, path, server.name)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"status": "uploaded", "filename": file.filename}

@router.post("/upload-folder")
async def upload_folder(server_id: int, path: str = "", files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    upload_dir = safe_path(server_id, path, server.name)
    os.makedirs(upload_dir, exist_ok=True)

    uploaded = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        uploaded.append(file.filename)

    return {"status": "uploaded", "count": len(uploaded), "files": uploaded}

@router.delete("/")
def delete_file(server_id: int, path: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    file_path = safe_path(server_id, path, server.name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Path not found")

    if os.path.isdir(file_path):
        shutil.rmtree(file_path)
    else:
        os.remove(file_path)
    return {"status": "deleted"}

class FolderCreate(BaseModel):
    path: str

@router.post("/mkdir")
def create_folder(server_id: int, folder: FolderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    dir_path = safe_path(server_id, folder.path, server.name)
    os.makedirs(dir_path, exist_ok=True)
    return {"status": "created", "path": folder.path}

@router.post("/backup")
def create_backup(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server_dir = get_server_dir(server_id, server.name)
    backups_dir = os.path.join(server_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{server.name}_{timestamp}.zip"
    backup_path = os.path.join(backups_dir, backup_name)

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(server_dir):
            if "backups" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, server_dir)
                zipf.write(file_path, arcname)

    backup_size = os.path.getsize(backup_path)
    return {"status": "created", "filename": backup_name, "size": backup_size}

@router.get("/backups")
def list_backups(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backups_dir = os.path.join(get_server_dir(server_id, server.name), "backups")
    if not os.path.exists(backups_dir):
        return []

    backups = []
    for file in os.listdir(backups_dir):
        if file.endswith(".zip"):
            file_path = os.path.join(backups_dir, file)
            backups.append({
                "filename": file,
                "size": os.path.getsize(file_path),
                "created": os.path.getmtime(file_path)
            })
    backups.sort(key=lambda x: x["created"], reverse=True)
    return backups

@router.get("/backups/{filename}/download")
def download_backup(server_id: int, filename: str, token: str = None, db: Session = Depends(get_db)):
    from jose import JWTError, jwt
    from config import SECRET_KEY, ALGORITHM
    from models.user import User

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backup_path = os.path.join(get_server_dir(server_id, server.name), "backups", filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    return FileResponse(backup_path, filename=filename)

@router.post("/restore/{filename}")
def restore_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backup_path = os.path.join(get_server_dir(server_id, server.name), "backups", filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    if server.status == "running":
        raise HTTPException(status_code=400, detail="Stop server before restoring")

    server_dir = get_server_dir(server_id, server.name)
    backups_dir = os.path.join(server_dir, "backups")

    temp_backup = os.path.join(server_dir, "_temp_backup.zip")
    shutil.copy2(backup_path, temp_backup)

    for item in os.listdir(server_dir):
        item_path = os.path.join(server_dir, item)
        if item == "backups":
            continue
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

    with zipfile.ZipFile(temp_backup, 'r') as zipf:
        zipf.extractall(server_dir)

    os.remove(temp_backup)
    return {"status": "restored", "filename": filename}

@router.delete("/backups/{filename}")
def delete_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backup_path = os.path.join(get_server_dir(server_id, server.name), "backups", filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    os.remove(backup_path)
    return {"status": "deleted"}
