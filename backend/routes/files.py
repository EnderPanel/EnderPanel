import os
import platform
import shutil
import stat
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
from utils.docker_client import get_docker_client
from config import SERVERS_DIR

router = APIRouter(prefix="/api/servers/{server_id}/files", tags=["files"])
IS_LINUX = platform.system() == "Linux"
FILE_HELPER_IMAGE = os.getenv("FILE_HELPER_IMAGE", "mc-panel-server:latest")

def sanitize_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def get_server_dir(server_id: int, server_name: str = None):
    if server_name:
        return os.path.join(SERVERS_DIR, f"{server_id}-{sanitize_name(server_name)}")
    for folder in os.listdir(SERVERS_DIR):
        if folder.startswith(f"{server_id}-"):
            return os.path.join(SERVERS_DIR, folder)
    return os.path.join(SERVERS_DIR, str(server_id))


def _safe_join(root: str, path: str = "", detail: str = "Invalid path") -> str:
    root_real = os.path.realpath(root)
    full_path = os.path.realpath(os.path.join(root_real, path or ""))
    try:
        inside_root = os.path.commonpath([root_real, full_path]) == root_real
    except ValueError:
        inside_root = False
    if not inside_root:
        raise HTTPException(status_code=400, detail=detail)
    return full_path


def safe_path(server_id: int, path: str, server_name: str = None) -> str:
    return _safe_join(get_server_dir(server_id, server_name), path, "Invalid path")


def safe_upload_path(upload_dir: str, filename: str | None, allow_relative: bool = False) -> str:
    raw_name = (filename or "").replace("\\", "/")
    if allow_relative:
        raw_name = raw_name.lstrip("/")
        parts = raw_name.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise HTTPException(status_code=400, detail="Invalid upload filename")
        relative_name = os.path.join(*parts)
    else:
        relative_name = os.path.basename(raw_name)
        if relative_name in ("", ".", ".."):
            raise HTTPException(status_code=400, detail="Invalid upload filename")

    return _safe_join(upload_dir, relative_name, "Invalid upload filename")

def _local_fix_permissions(path: str) -> bool:
    success = True
    try:
        if os.path.isdir(path):
            os.chmod(path, 0o777)
            for root, dirs, files in os.walk(path):
                for name in dirs:
                    try:
                        os.chmod(os.path.join(root, name), 0o777)
                    except PermissionError:
                        success = False
                for name in files:
                    try:
                        os.chmod(os.path.join(root, name), 0o666)
                    except PermissionError:
                        success = False
        else:
            os.chmod(path, 0o666)
    except PermissionError:
        success = False
    except FileNotFoundError:
        return True
    return success

def _docker_fix_permissions(path: str) -> bool:
    if not IS_LINUX or not os.path.exists(path):
        return False

    try:
        get_docker_client().containers.run(
            FILE_HELPER_IMAGE,
            command=["sh", "-lc", "chmod -R a+rwX /target || true"],
            remove=True,
            volumes={os.path.abspath(path): {"bind": "/target", "mode": "rw"}},
        )
        return True
    except Exception:
        return False

def fix_permissions(path: str) -> None:
    """Fix Docker-owned file permissions so the backend user can read/write."""
    if not os.path.exists(path):
        return
    if _local_fix_permissions(path):
        return
    _docker_fix_permissions(path)

def _retry_after_fix(path: str, action):
    try:
        return action()
    except PermissionError:
        fix_permissions(path)
        return action()

def _docker_remove(path: str) -> bool:
    if not IS_LINUX or not os.path.exists(path):
        return False
    parent = os.path.dirname(os.path.abspath(path))
    name = os.path.basename(path)
    try:
        get_docker_client().containers.run(
            FILE_HELPER_IMAGE,
            command=["rm", "-rf", f"/target/{name}"],
            remove=True,
            volumes={parent: {"bind": "/target", "mode": "rw"}},
        )
        return not os.path.exists(path)
    except Exception:
        return False

def sudo_remove(path: str) -> None:
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except PermissionError:
        fix_permissions(path)
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except PermissionError:
            if not _docker_remove(path):
                raise

def sudo_write(path: str, content: bytes) -> None:
    def write():
        with open(path, "wb") as f:
            f.write(content)
    _retry_after_fix(path, write)

def sudo_write_text(path: str, content: str) -> None:
    def write():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    _retry_after_fix(path, write)


def _safe_backup_path(server_id: int, server_name: str, filename: str) -> str:
    if filename != os.path.basename(filename):
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    backups_dir = os.path.join(get_server_dir(server_id, server_name), "backups")
    return _safe_join(backups_dir, filename, "Invalid backup filename")


def _safe_extract_zip(zipf: zipfile.ZipFile, destination: str) -> None:
    destination_root = os.path.realpath(destination)
    for member in zipf.infolist():
        member_name = member.filename
        if not member_name or member_name.startswith("/") or os.path.isabs(member_name):
            raise HTTPException(status_code=400, detail="Backup contains invalid paths")

        mode = member.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise HTTPException(status_code=400, detail="Backup contains unsupported links")

        target_path = os.path.realpath(os.path.join(destination_root, member_name))
        try:
            inside_destination = os.path.commonpath([destination_root, target_path]) == destination_root
        except ValueError:
            inside_destination = False
        if not inside_destination:
            raise HTTPException(status_code=400, detail="Backup contains unsafe paths")

    zipf.extractall(destination)

@router.get("/")
def list_files(server_id: int, path: str = "", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    dir_path = safe_path(server_id, path, server.name)
    if not os.path.exists(dir_path):
        if path:
            raise HTTPException(status_code=404, detail="Path not found")
        os.makedirs(dir_path, exist_ok=True)
    fix_permissions(dir_path)

    items = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        try:
            is_dir = os.path.isdir(item_path)
            size = os.path.getsize(item_path) if not is_dir else 0
            modified = os.path.getmtime(item_path)
        except PermissionError:
            is_dir = False
            size = 0
            modified = 0
        items.append({"name": item, "is_dir": is_dir, "size": size, "modified": modified})
    return items

@router.get("/read")
def read_file(server_id: int, path: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    file_path = safe_path(server_id, path, server.name)
    fix_permissions(file_path)
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
    fix_permissions(os.path.dirname(file_path))
    sudo_write_text(file_path, file.content)
    return {"status": "saved", "path": file.path}

@router.post("/upload")
async def upload_file(server_id: int, path: str = "", file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    upload_dir = safe_path(server_id, path, server.name)
    os.makedirs(upload_dir, exist_ok=True)
    fix_permissions(upload_dir)
    content = await file.read()
    upload_path = safe_upload_path(upload_dir, file.filename)
    sudo_write(upload_path, content)
    return {"status": "uploaded", "filename": file.filename}

@router.post("/upload-folder")
async def upload_folder(server_id: int, path: str = "", files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    upload_dir = safe_path(server_id, path, server.name)
    os.makedirs(upload_dir, exist_ok=True)
    fix_permissions(upload_dir)

    uploaded = []
    for file in files:
        file_path = safe_upload_path(upload_dir, file.filename, allow_relative=True)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        fix_permissions(os.path.dirname(file_path))
        sudo_write(file_path, await file.read())
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

    fix_permissions(file_path)
    sudo_remove(file_path)
    return {"status": "deleted"}

class FolderCreate(BaseModel):
    path: str

@router.post("/mkdir")
def create_folder(server_id: int, folder: FolderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    dir_path = safe_path(server_id, folder.path, server.name)
    fix_permissions(os.path.dirname(dir_path))
    os.makedirs(dir_path, exist_ok=True)
    return {"status": "created", "path": folder.path}

@router.post("/backup")
def create_backup(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    server_dir = get_server_dir(server_id, server.name)
    fix_permissions(server_dir)
    backups_dir = os.path.join(server_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{sanitize_name(server.name)}_{timestamp}.zip"
    backup_path = os.path.join(backups_dir, backup_name)

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(server_dir):
            if "backups" in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, server_dir)
                try:
                    zipf.write(file_path, arcname)
                except PermissionError:
                    pass

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
    fix_permissions(backups_dir)

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
def download_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backup_path = _safe_backup_path(server_id, server.name, filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    return FileResponse(backup_path, filename=filename)

@router.post("/restore/{filename}")
def restore_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backup_path = _safe_backup_path(server_id, server.name, filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    if server.status == "running":
        raise HTTPException(status_code=400, detail="Stop server before restoring")

    server_dir = get_server_dir(server_id, server.name)
    backups_dir = os.path.join(server_dir, "backups")
    fix_permissions(server_dir)
    fix_permissions(backups_dir)

    temp_backup = os.path.join(server_dir, "_temp_backup.zip")
    shutil.copy2(backup_path, temp_backup)

    for item in os.listdir(server_dir):
        item_path = os.path.join(server_dir, item)
        if item == "backups":
            continue
        sudo_remove(item_path)

    try:
        with zipfile.ZipFile(temp_backup, 'r') as zipf:
            _safe_extract_zip(zipf, server_dir)
    finally:
        if os.path.exists(temp_backup):
            sudo_remove(temp_backup)

    return {"status": "restored", "filename": filename}

@router.delete("/backups/{filename}")
def delete_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    backup_path = _safe_backup_path(server_id, server.name, filename)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="Backup not found")

    fix_permissions(backup_path)
    sudo_remove(backup_path)
    return {"status": "deleted"}
