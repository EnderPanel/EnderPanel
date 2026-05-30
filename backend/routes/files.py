import hashlib
import json
import os
import platform
import shutil
import stat
import tempfile
import zipfile
import time
import re
from contextlib import suppress
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from models.user import User
from models.server import Server
from models.panel_setting import PanelSetting
from utils.security import get_current_user
from utils.docker_client import get_docker_client
from config import SERVERS_DIR

router = APIRouter(prefix="/api/servers/{server_id}/files", tags=["files"])
IS_LINUX = platform.system() == "Linux"
FILE_HELPER_IMAGE = os.getenv("FILE_HELPER_IMAGE", "mc-panel-server:latest")
FILE_HELPER_PREFIX = "mc-panel-helper"
DEDUP_DIR_NAME = ".dedup"
DEDUP_MANIFEST_VERSION = 1
DEFAULT_UPLOAD_LIMIT_BYTES = int(os.getenv("ENDERPANEL_UPLOAD_LIMIT_MB", "100")) * 1024 * 1024
TEXT_EDIT_LIMIT_BYTES = int(os.getenv("ENDERPANEL_EDITOR_LIMIT_MB", "2")) * 1024 * 1024
SEARCH_MAX_RESULTS = 200
UPLOAD_LIMIT_KEY = "upload_limit_mb"


def _helper_container_name(purpose: str) -> str:
    return f"{FILE_HELPER_PREFIX}-{purpose}-{os.getpid()}-{time.time_ns()}"

def sanitize_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)


def get_server_dir(server_id: int, server_name: str = None):
    exact_path = None
    if server_name:
        exact_path = os.path.join(SERVERS_DIR, f"{server_id}-{sanitize_name(server_name)}")
        if os.path.exists(exact_path):
            return exact_path

    for folder in sorted(os.listdir(SERVERS_DIR)):
        if folder.startswith(f"{server_id}-"):
            return os.path.join(SERVERS_DIR, folder)

    if exact_path:
        return exact_path
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


def _ensure_not_reserved_backup_path(path: str) -> None:
    normalized = (path or "").replace("\\", "/").strip("/")
    if not normalized:
        return
    if DEDUP_DIR_NAME in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Reserved backup path")


def safe_path(server_id: int, path: str, server_name: str = None) -> str:
    _ensure_not_reserved_backup_path(path)
    return _safe_join(get_server_dir(server_id, server_name), path, "Invalid path")


def safe_upload_path(upload_dir: str, filename: str | None, allow_relative: bool = False) -> str:
    raw_name = (filename or "").replace("\\", "/")
    if allow_relative:
        raw_name = raw_name.lstrip("/")
        parts = raw_name.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise HTTPException(status_code=400, detail="Invalid upload filename")
        if DEDUP_DIR_NAME in parts:
            raise HTTPException(status_code=400, detail="Reserved backup path")
        relative_name = os.path.join(*parts)
    else:
        relative_name = os.path.basename(raw_name)
        if relative_name in ("", ".", ".."):
            raise HTTPException(status_code=400, detail="Invalid upload filename")

    return _safe_join(upload_dir, relative_name, "Invalid upload filename")


def get_server_for_user(server_id: int, current_user: User, db: Session) -> Server:
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


def is_probably_binary(content: bytes) -> bool:
    if not content:
        return False
    sample = content[:4096]
    if b"\x00" in sample:
        return True
    text_chars = set(b"\t\n\r\f\b") | set(range(32, 127))
    suspicious = sum(byte not in text_chars for byte in sample)
    return suspicious / max(len(sample), 1) > 0.30


def _sanitize_archive_name(value: str) -> str:
    name = os.path.basename((value or "").strip())
    if name in ("", ".", ".."):
        raise HTTPException(status_code=400, detail="Invalid archive name")
    if not name.lower().endswith(".zip"):
        name = f"{name}.zip"
    return name


def _write_path_to_zip(zipf: zipfile.ZipFile, source_path: str, archive_name: str) -> None:
    if os.path.isdir(source_path):
        added_entry = False
        for root, dirs, files in os.walk(source_path):
            dirs[:] = [name for name in dirs if name != DEDUP_DIR_NAME]
            rel_root = os.path.relpath(root, source_path)
            archive_root = archive_name if rel_root == "." else f"{archive_name}/{rel_root.replace(os.sep, '/')}"
            if rel_root == "." and not dirs and not files:
                zipf.writestr(f"{archive_name}/", b"")
                added_entry = True
            for dir_name in dirs:
                zipf.writestr(f"{archive_root}/{dir_name}/", b"")
                added_entry = True
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if os.path.islink(file_path):
                    continue
                rel_file = file_name if rel_root == "." else f"{rel_root.replace(os.sep, '/')}/{file_name}"
                zipf.write(file_path, arcname=f"{archive_name}/{rel_file}")
                added_entry = True
        if not added_entry:
            zipf.writestr(f"{archive_name}/", b"")
        return

    zipf.write(source_path, arcname=archive_name)


def get_upload_limit_bytes(db: Session | None = None) -> int:
    owns_session = db is None
    if db is None:
        from database import SessionLocal
        db = SessionLocal()
    try:
        setting = db.query(PanelSetting).filter(PanelSetting.key == UPLOAD_LIMIT_KEY).first()
        if not setting:
            return DEFAULT_UPLOAD_LIMIT_BYTES
        value_mb = int(setting.value)
        if value_mb < 1:
            return DEFAULT_UPLOAD_LIMIT_BYTES
        return value_mb * 1024 * 1024
    except Exception:
        return DEFAULT_UPLOAD_LIMIT_BYTES
    finally:
        if owns_session:
            db.close()


def ensure_upload_size(content: bytes, limit_bytes: int) -> None:
    if len(content) > limit_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File must be under {max(1, limit_bytes // (1024 * 1024))}MB",
        )

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
            name=_helper_container_name("chmod"),
            command=["sh", "-lc", "chmod -R a+rwX /target || true"],
            remove=True,
            labels={"enderpanel.helper": "true", "enderpanel.purpose": "chmod"},
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
            name=_helper_container_name("rm"),
            command=["rm", "-rf", f"/target/{name}"],
            remove=True,
            labels={"enderpanel.helper": "true", "enderpanel.purpose": "rm"},
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


def _backups_dir(server_id: int, server_name: str) -> str:
    return os.path.join(get_server_dir(server_id, server_name), "backups")


def _dedup_root(backups_dir: str) -> str:
    return os.path.join(backups_dir, DEDUP_DIR_NAME)


def _dedup_blobs_dir(backups_dir: str) -> str:
    return os.path.join(_dedup_root(backups_dir), "blobs")


def _dedup_manifests_dir(backups_dir: str) -> str:
    return os.path.join(_dedup_root(backups_dir), "manifests")


def _dedup_manifest_name(filename: str) -> str:
    return f"{filename}.json"


def _dedup_manifest_path(backups_dir: str, filename: str) -> str:
    return os.path.join(_dedup_manifests_dir(backups_dir), _dedup_manifest_name(filename))


def _ensure_dedup_dirs(backups_dir: str) -> None:
    os.makedirs(_dedup_blobs_dir(backups_dir), exist_ok=True)
    os.makedirs(_dedup_manifests_dir(backups_dir), exist_ok=True)


def _hash_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _store_blob_if_missing(backups_dir: str, digest: str, source_path: str) -> None:
    blobs_dir = _dedup_blobs_dir(backups_dir)
    blob_path = os.path.join(blobs_dir, digest)
    if os.path.exists(blob_path):
        return

    temp_path = f"{blob_path}.tmp-{os.getpid()}-{time.time_ns()}"
    shutil.copy2(source_path, temp_path)
    try:
        os.replace(temp_path, blob_path)
    except FileExistsError:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _blob_path(backups_dir: str, digest: str) -> str:
    return os.path.join(_dedup_blobs_dir(backups_dir), digest)


def _iter_server_snapshot_entries(server_dir: str):
    for root, dirs, files in os.walk(server_dir):
        dirs[:] = [name for name in dirs if name != "backups"]
        rel_root = os.path.relpath(root, server_dir)
        if rel_root != ".":
            stat_result = os.stat(root)
            yield {
                "type": "dir",
                "path": rel_root,
                "mode": stat.S_IMODE(stat_result.st_mode),
                "mtime": stat_result.st_mtime,
            }

        for file_name in files:
            file_path = os.path.join(root, file_name)
            if os.path.islink(file_path):
                continue
            rel_path = os.path.relpath(file_path, server_dir)
            stat_result = os.stat(file_path)
            digest = _hash_file(file_path)
            yield {
                "type": "file",
                "path": rel_path,
                "hash": digest,
                "size": stat_result.st_size,
                "mode": stat.S_IMODE(stat_result.st_mode),
                "mtime": stat_result.st_mtime,
                "source_path": file_path,
            }


def _write_dedup_manifest(backups_dir: str, filename: str, manifest: dict) -> None:
    manifest_path = _dedup_manifest_path(backups_dir, filename)
    sudo_write_text(manifest_path, json.dumps(manifest, ensure_ascii=True, indent=2))


def _load_dedup_manifest(backups_dir: str, filename: str) -> dict | None:
    manifest_path = _dedup_manifest_path(backups_dir, filename)
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _list_dedup_backups(backups_dir: str) -> list[dict]:
    manifests_dir = _dedup_manifests_dir(backups_dir)
    if not os.path.exists(manifests_dir):
        return []

    items = []
    for file_name in os.listdir(manifests_dir):
        if not file_name.endswith(".json"):
            continue
        manifest_path = os.path.join(manifests_dir, file_name)
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        except Exception:
            continue
        snapshot_name = str(manifest.get("filename") or file_name[:-5])
        items.append({
            "filename": snapshot_name,
            "size": int(manifest.get("logical_size") or 0),
            "created": float(manifest.get("created_ts") or os.path.getmtime(manifest_path)),
            "notes": manifest.get("notes"),
        })
    return items


def _garbage_collect_dedup_blobs(backups_dir: str) -> None:
    manifests_dir = _dedup_manifests_dir(backups_dir)
    blobs_dir = _dedup_blobs_dir(backups_dir)
    if not os.path.exists(manifests_dir) or not os.path.exists(blobs_dir):
        return

    referenced = set()
    for file_name in os.listdir(manifests_dir):
        if not file_name.endswith(".json"):
            continue
        manifest_path = os.path.join(manifests_dir, file_name)
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        except Exception:
            continue
        for entry in manifest.get("entries", []):
            if entry.get("type") == "file" and entry.get("hash"):
                referenced.add(entry["hash"])

    for blob_name in os.listdir(blobs_dir):
        blob_path = os.path.join(blobs_dir, blob_name)
        if blob_name not in referenced and os.path.isfile(blob_path):
            sudo_remove(blob_path)


def _restore_from_dedup_manifest(server_dir: str, backups_dir: str, manifest: dict) -> None:
    entries = manifest.get("entries", [])
    if not isinstance(entries, list):
        raise HTTPException(status_code=400, detail="Backup manifest is invalid")

    for entry in entries:
        if entry.get("type") != "dir":
            continue
        rel_path = entry.get("path")
        if not isinstance(rel_path, str):
            raise HTTPException(status_code=400, detail="Backup manifest is invalid")
        dir_path = _safe_join(server_dir, rel_path, "Backup contains unsafe paths")
        os.makedirs(dir_path, exist_ok=True)
        mode = entry.get("mode")
        if isinstance(mode, int):
            with suppress(Exception):
                os.chmod(dir_path, mode)

    for entry in entries:
        if entry.get("type") != "file":
            continue
        rel_path = entry.get("path")
        digest = entry.get("hash")
        if not isinstance(rel_path, str) or not isinstance(digest, str):
            raise HTTPException(status_code=400, detail="Backup manifest is invalid")
        target_path = _safe_join(server_dir, rel_path, "Backup contains unsafe paths")
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        blob_path = _blob_path(backups_dir, digest)
        if not os.path.exists(blob_path):
            raise HTTPException(status_code=400, detail=f"Backup blob missing for {rel_path}")
        shutil.copy2(blob_path, target_path)
        mode = entry.get("mode")
        if isinstance(mode, int):
            with suppress(Exception):
                os.chmod(target_path, mode)
        mtime = entry.get("mtime")
        if isinstance(mtime, (int, float)):
            with suppress(Exception):
                os.utime(target_path, (mtime, mtime))


def _build_zip_from_manifest(backups_dir: str, manifest: dict, destination: str) -> None:
    entries = manifest.get("entries", [])
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zipf:
        for entry in entries:
            rel_path = entry.get("path")
            if not isinstance(rel_path, str):
                continue
            if entry.get("type") == "dir":
                info = zipfile.ZipInfo(rel_path.rstrip("/") + "/")
                info.date_time = time.localtime(entry.get("mtime") or time.time())[:6]
                info.external_attr = ((entry.get("mode") or 0o755) & 0xFFFF) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                zipf.writestr(info, b"")
                continue

            if entry.get("type") != "file":
                continue
            digest = entry.get("hash")
            if not isinstance(digest, str):
                continue
            blob_path = _blob_path(backups_dir, digest)
            if not os.path.exists(blob_path):
                raise HTTPException(status_code=400, detail=f"Backup blob missing for {rel_path}")
            info = zipfile.ZipInfo(rel_path)
            info.date_time = time.localtime(entry.get("mtime") or time.time())[:6]
            info.external_attr = ((entry.get("mode") or 0o644) & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(blob_path, "rb") as handle, zipf.open(info, "w") as destination_handle:
                shutil.copyfileobj(handle, destination_handle, length=1024 * 1024)


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
    server = get_server_for_user(server_id, current_user, db)

    dir_path = safe_path(server_id, path, server.name)
    if not os.path.exists(dir_path):
        if path:
            raise HTTPException(status_code=404, detail="Path not found")
        os.makedirs(dir_path, exist_ok=True)
    fix_permissions(dir_path)

    items = []
    for item in os.listdir(dir_path):
        if item == DEDUP_DIR_NAME:
            continue
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


@router.get("/limits")
def file_limits(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    get_server_for_user(server_id, current_user, db)
    upload_limit_bytes = get_upload_limit_bytes(db)
    return {
        "upload_limit_bytes": upload_limit_bytes,
        "text_edit_limit_bytes": TEXT_EDIT_LIMIT_BYTES,
        "search_max_results": SEARCH_MAX_RESULTS,
    }


@router.get("/search")
def search_files(
    server_id: int,
    query: str,
    path: str = "",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, current_user, db)
    search_root = safe_path(server_id, path, server.name)
    if not os.path.isdir(search_root):
        raise HTTPException(status_code=404, detail="Path not found")

    needle = query.strip().lower()
    if len(needle) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

    server_root = get_server_dir(server_id, server.name)
    results = []
    for root, dirs, files in os.walk(search_root):
        dirs[:] = [name for name in dirs if name != DEDUP_DIR_NAME]
        for name, is_dir in [(dir_name, True) for dir_name in dirs] + [(file_name, False) for file_name in files]:
            if needle not in name.lower():
                continue
            item_path = os.path.join(root, name)
            relative_path = os.path.relpath(item_path, server_root).replace("\\", "/")
            try:
                size = 0 if is_dir else os.path.getsize(item_path)
                modified = os.path.getmtime(item_path)
            except OSError:
                size = 0
                modified = 0
            results.append({
                "name": name,
                "path": relative_path,
                "parent": os.path.dirname(relative_path).replace("\\", "/"),
                "is_dir": is_dir,
                "size": size,
                "modified": modified,
            })
            if len(results) >= SEARCH_MAX_RESULTS:
                return {"results": results, "truncated": True}
    return {"results": results, "truncated": False}

@router.get("/read")
def read_file(server_id: int, path: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

    file_path = safe_path(server_id, path, server.name)
    fix_permissions(file_path)
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    size = os.path.getsize(file_path)
    if size > TEXT_EDIT_LIMIT_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File is too large to edit in the panel. Limit: {TEXT_EDIT_LIMIT_BYTES // (1024 * 1024)}MB",
        )

    with open(file_path, "rb") as f:
        content = f.read()
    if is_probably_binary(content):
        raise HTTPException(status_code=400, detail="This file looks binary and cannot be edited in the text editor")
    return {"content": content.decode("utf-8", errors="replace"), "path": path, "size": size}

class FileWrite(BaseModel):
    path: str
    content: str


class FileRename(BaseModel):
    path: str
    new_name: str


class FileArchive(BaseModel):
    path: str = ""
    items: List[str]
    output_name: str


class FileExtract(BaseModel):
    path: str

@router.post("/write")
def write_file(server_id: int, file: FileWrite, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

    file_path = safe_path(server_id, file.path, server.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    fix_permissions(os.path.dirname(file_path))
    sudo_write_text(file_path, file.content)
    return {"status": "saved", "path": file.path}


@router.post("/rename")
def rename_file(server_id: int, payload: FileRename, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)
    source_path = safe_path(server_id, payload.path, server.name)
    if not os.path.exists(source_path):
        raise HTTPException(status_code=404, detail="Path not found")

    new_name = os.path.basename((payload.new_name or "").strip())
    if new_name in ("", ".", ".."):
        raise HTTPException(status_code=400, detail="Invalid new name")

    destination_path = _safe_join(os.path.dirname(source_path), new_name, "Invalid new name")
    if os.path.exists(destination_path) and os.path.realpath(destination_path) != os.path.realpath(source_path):
        raise HTTPException(status_code=400, detail="A file or folder with that name already exists")

    fix_permissions(source_path)
    fix_permissions(os.path.dirname(source_path))
    os.rename(source_path, destination_path)
    rel_path = os.path.relpath(destination_path, get_server_dir(server_id, server.name)).replace("\\", "/")
    return {"status": "renamed", "path": rel_path}


@router.post("/archive")
def archive_files(server_id: int, payload: FileArchive, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)
    if not payload.items:
        raise HTTPException(status_code=400, detail="Select at least one file or folder to archive")

    destination_dir = safe_path(server_id, payload.path, server.name)
    os.makedirs(destination_dir, exist_ok=True)
    archive_name = _sanitize_archive_name(payload.output_name)
    output_path = safe_upload_path(destination_dir, archive_name)
    server_root = get_server_dir(server_id, server.name)

    fix_permissions(destination_dir)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for item in payload.items:
            source_path = safe_path(server_id, item, server.name)
            if not os.path.exists(source_path):
                raise HTTPException(status_code=404, detail=f"Path not found: {item}")
            if os.path.realpath(source_path) == os.path.realpath(output_path):
                raise HTTPException(status_code=400, detail="Archive cannot include itself")
            archive_entry_name = os.path.basename(source_path.rstrip("/")) or os.path.basename(item.rstrip("/"))
            _write_path_to_zip(zipf, source_path, archive_entry_name)

    rel_path = os.path.relpath(output_path, server_root).replace("\\", "/")
    return {"status": "archived", "path": rel_path, "filename": archive_name}


@router.post("/extract")
def extract_archive(server_id: int, payload: FileExtract, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)
    archive_path = safe_path(server_id, payload.path, server.name)
    if not os.path.exists(archive_path) or not os.path.isfile(archive_path):
        raise HTTPException(status_code=404, detail="Archive not found")
    if not archive_path.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP archives can be extracted right now")

    destination_dir = os.path.dirname(archive_path)
    fix_permissions(archive_path)
    fix_permissions(destination_dir)
    with zipfile.ZipFile(archive_path, "r") as zipf:
        _safe_extract_zip(zipf, destination_dir)
    return {"status": "extracted"}

@router.post("/upload")
async def upload_file(
    server_id: int,
    path: str = "",
    relative_path: str | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, current_user, db)
    upload_limit_bytes = get_upload_limit_bytes(db)

    upload_dir = safe_path(server_id, path, server.name)
    os.makedirs(upload_dir, exist_ok=True)
    fix_permissions(upload_dir)
    content = await file.read()
    ensure_upload_size(content, upload_limit_bytes)
    upload_path = safe_upload_path(upload_dir, relative_path or file.filename, allow_relative=bool(relative_path))
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    sudo_write(upload_path, content)
    return {"status": "uploaded", "filename": relative_path or file.filename}

@router.post("/upload-folder")
async def upload_folder(server_id: int, path: str = "", files: List[UploadFile] = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)
    upload_limit_bytes = get_upload_limit_bytes(db)

    upload_dir = safe_path(server_id, path, server.name)
    os.makedirs(upload_dir, exist_ok=True)
    fix_permissions(upload_dir)

    uploaded = []
    for file in files:
        file_path = safe_upload_path(upload_dir, file.filename, allow_relative=True)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        fix_permissions(os.path.dirname(file_path))
        content = await file.read()
        ensure_upload_size(content, upload_limit_bytes)
        sudo_write(file_path, content)
        uploaded.append(file.filename)

    return {"status": "uploaded", "count": len(uploaded), "files": uploaded}

@router.delete("/")
def delete_file(server_id: int, path: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

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
    server = get_server_for_user(server_id, current_user, db)

    dir_path = safe_path(server_id, folder.path, server.name)
    fix_permissions(os.path.dirname(dir_path))
    os.makedirs(dir_path, exist_ok=True)
    return {"status": "created", "path": folder.path}

class BackupCreate(BaseModel):
    notes: Optional[str] = None


@router.post("/backup")
def create_backup(
    server_id: int,
    payload: BackupCreate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, current_user, db)

    server_dir = get_server_dir(server_id, server.name)
    fix_permissions(server_dir)
    backups_dir = _backups_dir(server_id, server.name)
    os.makedirs(backups_dir, exist_ok=True)
    _ensure_dedup_dirs(backups_dir)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{sanitize_name(server.name)}_{timestamp}.zip"

    entries = []
    logical_size = 0
    new_blob_bytes = 0

    for entry in _iter_server_snapshot_entries(server_dir):
        if entry["type"] == "file":
            logical_size += int(entry.get("size") or 0)
            digest = entry["hash"]
            blob_path = _blob_path(backups_dir, digest)
            if not os.path.exists(blob_path):
                new_blob_bytes += int(entry.get("size") or 0)
            _store_blob_if_missing(backups_dir, digest, entry.pop("source_path"))
        entries.append(entry)

    manifest = {
        "version": DEDUP_MANIFEST_VERSION,
        "filename": backup_name,
        "server_id": server_id,
        "server_name": server.name,
        "created_ts": time.time(),
        "logical_size": logical_size,
        "new_blob_bytes": new_blob_bytes,
        "entries": entries,
        "notes": payload.notes if payload and payload.notes else None,
    }
    _write_dedup_manifest(backups_dir, backup_name, manifest)
    manifest_size = os.path.getsize(_dedup_manifest_path(backups_dir, backup_name))
    return {
        "status": "created",
        "filename": backup_name,
        "size": logical_size,
        "storage_size": manifest_size + new_blob_bytes,
        "deduplicated": True,
    }

@router.get("/backups")
def list_backups(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

    backups_dir = _backups_dir(server_id, server.name)
    if not os.path.exists(backups_dir):
        return []
    fix_permissions(backups_dir)

    backups = _list_dedup_backups(backups_dir)
    for file in os.listdir(backups_dir):
        if file.endswith(".zip"):
            file_path = os.path.join(backups_dir, file)
            backups.append({
                "filename": file,
                "size": os.path.getsize(file_path),
                "created": os.path.getmtime(file_path),
                "notes": None,
            })
    backups.sort(key=lambda x: x["created"], reverse=True)
    return backups

@router.get("/backups/{filename}/download")
def download_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

    backups_dir = _backups_dir(server_id, server.name)
    backup_path = _safe_backup_path(server_id, server.name, filename)
    if os.path.exists(backup_path):
        return FileResponse(backup_path, filename=filename)

    manifest = _load_dedup_manifest(backups_dir, filename)
    if not manifest:
        raise HTTPException(status_code=404, detail="Backup not found")

    temp_file = tempfile.NamedTemporaryFile(prefix="enderpanel-backup-", suffix=".zip", delete=False)
    temp_file.close()
    _build_zip_from_manifest(backups_dir, manifest, temp_file.name)
    return FileResponse(
        temp_file.name,
        filename=filename,
        background=BackgroundTask(lambda path=temp_file.name: os.path.exists(path) and os.remove(path)),
    )

@router.post("/restore/{filename}")
def restore_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

    if server.status == "running":
        raise HTTPException(status_code=400, detail="Stop server before restoring")

    server_dir = get_server_dir(server_id, server.name)
    backups_dir = _backups_dir(server_id, server.name)
    fix_permissions(server_dir)
    fix_permissions(backups_dir)

    for item in os.listdir(server_dir):
        item_path = os.path.join(server_dir, item)
        if item == "backups":
            continue
        sudo_remove(item_path)

    backup_path = _safe_backup_path(server_id, server.name, filename)
    if os.path.exists(backup_path):
        temp_backup = os.path.join(server_dir, "_temp_backup.zip")
        shutil.copy2(backup_path, temp_backup)
        try:
            with zipfile.ZipFile(temp_backup, 'r') as zipf:
                _safe_extract_zip(zipf, server_dir)
        finally:
            if os.path.exists(temp_backup):
                sudo_remove(temp_backup)
    else:
        manifest = _load_dedup_manifest(backups_dir, filename)
        if not manifest:
            raise HTTPException(status_code=404, detail="Backup not found")
        _restore_from_dedup_manifest(server_dir, backups_dir, manifest)

    return {"status": "restored", "filename": filename}

class BackupNotesUpdate(BaseModel):
    notes: Optional[str] = None

@router.patch("/backups/{filename}/notes")
def update_backup_notes(
    server_id: int,
    filename: str,
    payload: BackupNotesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = get_server_for_user(server_id, current_user, db)
    backups_dir = _backups_dir(server_id, server.name)
    manifest_path = _dedup_manifest_path(backups_dir, filename)

    # Also check for zip file in case notes are missing
    backup_path = _safe_backup_path(server_id, server.name, filename)

    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        manifest["notes"] = payload.notes
        sudo_write_text(manifest_path, json.dumps(manifest, ensure_ascii=True, indent=2))
        return {"status": "updated", "notes": payload.notes}

    raise HTTPException(status_code=404, detail="Backup not found")

@router.delete("/backups/{filename}")
def delete_backup(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = get_server_for_user(server_id, current_user, db)

    backups_dir = _backups_dir(server_id, server.name)
    backup_path = _safe_backup_path(server_id, server.name, filename)
    manifest_path = _dedup_manifest_path(backups_dir, filename)

    if os.path.exists(backup_path):
        fix_permissions(backup_path)
        sudo_remove(backup_path)
        return {"status": "deleted"}

    if os.path.exists(manifest_path):
        fix_permissions(manifest_path)
        sudo_remove(manifest_path)
        _garbage_collect_dedup_blobs(backups_dir)
        return {"status": "deleted"}

    raise HTTPException(status_code=404, detail="Backup not found")
