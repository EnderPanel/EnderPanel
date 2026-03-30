import os
import shutil
import tempfile
import httpx
import tarfile
from fastapi import APIRouter, Depends, HTTPException
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/api/update", tags=["update"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
LATEST_URL = "https://enderpanel.space/latest.txt"
DOWNLOAD_URL = "https://enderpanel.space/releases/enderpanel-{}.tar.gz"

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

                # Copy new files first, then replace
                for item in os.listdir(extract_dir):
                    src = os.path.join(extract_dir, item)
                    dst = os.path.join(BASE_DIR, item)
                    tmp_dst = dst + ".new"
                    if os.path.isdir(src):
                        if os.path.exists(tmp_dst):
                            shutil.rmtree(tmp_dst)
                        shutil.copytree(src, tmp_dst)
                        if os.path.exists(dst):
                            shutil.rmtree(dst)
                        os.rename(tmp_dst, dst)
                    else:
                        shutil.copy2(src, dst)

            with open(VERSION_FILE, "w") as f:
                f.write(latest)

            return {"status": "updated", "version": latest}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Update failed: {str(e)}")
