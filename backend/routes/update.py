import os
import json
import shutil
import tempfile
import httpx
import tarfile
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/api/update", tags=["update"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
CONFIG_FILE = os.path.join(BASE_DIR, "backend", "data", "config.json")

DEFAULT_CONFIG = {
    "update_server": "https://enderpanel.space"
}

def load_config():
    try:
        return json.load(open(CONFIG_FILE))
    except:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_urls():
    config = load_config()
    base = config.get("update_server", "https://enderpanel.space").rstrip("/")
    return f"{base}/latest.txt", f"{base}/releases/enderpanel-{{}}.tar.gz"

def get_current_version():
    try:
        return open(VERSION_FILE).read().strip()
    except:
        return "0.0.0"

@router.get("/check")
async def check_update():
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(LATEST_URL)
            latest = r.text.strip()
            current = get_current_version()
            return {"current": current, "latest": latest, "update_available": latest != current}
    except:
        return {"current": get_current_version(), "latest": "unknown", "update_available": False}

@router.post("/install")
async def install_update(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    try:
        async with httpx.AsyncClient(timeout=300) as c:
            r = await c.get(LATEST_URL)
            latest = r.text.strip()

            download_url = DOWNLOAD_URL.format(latest)
            r = await c.get(download_url)
            if r.status_code != 200:
                raise HTTPException(500, "Failed to download update")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_tar = os.path.join(tmpdir, "update.tar.gz")
                with open(tmp_tar, "wb") as f:
                    f.write(r.content)

                extract_dir = os.path.join(tmpdir, "extract")
                os.makedirs(extract_dir)

                with tarfile.open(tmp_tar, "r:gz") as tar:
                    tar.extractall(extract_dir)

                # Files/dirs to preserve (user data)
                skip_dirs = {"servers", "avatars", "__pycache__"}
                skip_files = {"mcpanel.db"}

                def copytree_skip(src, dst):
                    """Copy directory, skipping user data."""
                    os.makedirs(dst, exist_ok=True)
                    for item in os.listdir(src):
                        s = os.path.join(src, item)
                        d = os.path.join(dst, item)
                        if item in skip_files:
                            continue
                        if item in skip_dirs:
                            continue
                        if os.path.isdir(s):
                            copytree_skip(s, d)
                        else:
                            shutil.copy2(s, d)

                # Copy new files, preserving user data
                for item in os.listdir(extract_dir):
                    src = os.path.join(extract_dir, item)
                    dst = os.path.join(BASE_DIR, item)
                    if item in skip_files:
                        continue
                    if item in skip_dirs:
                        continue
                    if os.path.isdir(src):
                        if os.path.exists(dst):
                            copytree_skip(src, dst)
                        else:
                            shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)

            with open(VERSION_FILE, "w") as f:
                f.write(latest)

            return {"status": "updated", "version": latest}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Update failed: {str(e)}")

class UpdateServerConfig(BaseModel):
    url: str

@router.get("/config")
def get_update_config(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    config = load_config()
    return {"update_server": config.get("update_server", "https://enderpanel.space")}

@router.post("/config")
def set_update_config(data: UpdateServerConfig, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    config = load_config()
    config["update_server"] = data.url.rstrip("/")
    save_config(config)
    return {"update_server": config["update_server"]}
