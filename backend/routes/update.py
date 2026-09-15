import os
import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
import re
import httpx
import tarfile
import hashlib
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/api/update", tags=["update"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
VERSION_FILE = os.path.join(BASE_DIR, "VERSION")
CONFIG_FILE = os.path.join(BASE_DIR, "backend", "data", "config.json")

DEFAULT_CONFIG = {
    "update_server": "https://raw.githubusercontent.com/EnderPanel/Releases/main"
}

GITHUB_RELEASES_BASE = "https://raw.githubusercontent.com/EnderPanel/Releases/main"
LEGACY_UPDATE_BASES = {
    "https://enderpanel.space",
    "http://enderpanel.space",
}
RUNTIME_IMAGES = (
    ("latest", "Dockerfile"),
    ("java8", "Dockerfile.java8"),
    ("java11", "Dockerfile.java11"),
    ("java17", "Dockerfile.java17"),
    ("java25", "Dockerfile.java25"),
)

def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as config_file:
            return json.load(config_file)
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

def get_urls():
    config = load_config()
    base = config.get("update_server", "https://enderpanel.space").rstrip("/")
    if base in LEGACY_UPDATE_BASES:
        base = GITHUB_RELEASES_BASE
    if "raw.githubusercontent.com/EnderPanel/Releases/main" in base or "github.com/EnderPanel/Releases/raw/main" in base:
        return f"{base}/latest.txt", f"{base}/enderpanel-{{}}.tar.gz"
    return f"{base}/latest.txt", f"{base}/releases/enderpanel-{{}}.tar.gz"

def get_current_version():
    try:
        with open(VERSION_FILE, "r", encoding="utf-8") as version_file:
            return version_file.read().strip()
    except Exception:
        return "0.0.0"


def parse_version(value: str) -> tuple[int, ...]:
    parts = re.findall(r"\d+", (value or "").strip())
    if not parts:
        return tuple()
    return tuple(int(part) for part in parts)


def is_newer_version(latest: str, current: str) -> bool:
    latest_parts = parse_version(latest)
    current_parts = parse_version(current)
    if not latest_parts:
        return False
    length = max(len(latest_parts), len(current_parts))
    latest_parts += (0,) * (length - len(latest_parts))
    current_parts += (0,) * (length - len(current_parts))
    return latest_parts > current_parts


def _path_inside(root: str, target: str) -> bool:
    root_real = os.path.realpath(root)
    target_real = os.path.realpath(target)
    try:
        return os.path.commonpath([root_real, target_real]) == root_real
    except ValueError:
        return False


def safe_extract_tar(tar: tarfile.TarFile, destination: str) -> None:
    for member in tar.getmembers():
        target = os.path.join(destination, member.name)
        if not _path_inside(destination, target):
            raise HTTPException(status_code=400, detail="Update archive contains unsafe paths")
        if member.issym() or member.islnk():
            raise HTTPException(status_code=400, detail="Update archive contains unsupported links")
        if not member.isdir() and not member.isfile():
            raise HTTPException(status_code=400, detail="Update archive contains unsupported special files")
    tar.extractall(destination, filter="data")


def _file_changed(source: str, destination: str) -> bool:
    if not os.path.isfile(source) or not os.path.isfile(destination):
        return os.path.isfile(source) != os.path.isfile(destination)
    with open(source, "rb") as source_file, open(destination, "rb") as destination_file:
        return hashlib.sha256(source_file.read()).digest() != hashlib.sha256(destination_file.read()).digest()


def _run_update_command(command: list[str], *, cwd: str, description: str) -> None:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"{description} could not start: {exc}") from exc
    if result.returncode != 0:
        output = (result.stderr or result.stdout or "unknown error").strip()[-2000:]
        raise HTTPException(status_code=500, detail=f"{description} failed: {output}")


def prepare_update_runtime(payload_dir: str) -> None:
    payload_backend = os.path.join(payload_dir, "backend")
    installed_backend = os.path.join(BASE_DIR, "backend")
    new_requirements = os.path.join(payload_backend, "requirements.txt")
    installed_requirements = os.path.join(installed_backend, "requirements.txt")
    if _file_changed(new_requirements, installed_requirements):
        _run_update_command(
            [sys.executable, "-m", "pip", "install", "-r", new_requirements],
            cwd=payload_backend,
            description="Installing backend dependencies",
        )

    changed_images = [
        (tag, dockerfile)
        for tag, dockerfile in RUNTIME_IMAGES
        if _file_changed(
            os.path.join(payload_backend, dockerfile),
            os.path.join(installed_backend, dockerfile),
        )
    ]
    if changed_images:
        docker = shutil.which("docker")
        if not docker:
            raise HTTPException(status_code=500, detail="Docker is required to rebuild updated Java images")
        for tag, dockerfile in changed_images:
            _run_update_command(
                [docker, "build", "-t", f"mc-panel-server:{tag}", "-f", dockerfile, "."],
                cwd=payload_backend,
                description=f"Building Java image {tag}",
            )


async def restart_panel_process() -> None:
    # BackgroundTasks runs after the response has been sent, so replacing the
    # process does not cut off the update response.
    await asyncio.sleep(0.5)
    main_path = os.path.join(BASE_DIR, "backend", "main.py")
    os.execv(sys.executable, [sys.executable, main_path])


def get_payload_dir(extract_dir: str) -> str:
    entries = [os.path.join(extract_dir, item) for item in os.listdir(extract_dir)]
    if len(entries) == 1 and os.path.isdir(entries[0]) and not os.path.exists(os.path.join(extract_dir, "backend")):
        return entries[0]
    return extract_dir


@router.get("/check")
async def check_update():
    try:
        latest_url, _ = get_urls()
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(latest_url)
            r.raise_for_status()
            latest = r.text.strip()
            current = get_current_version()
            return {"current": current, "latest": latest, "update_available": is_newer_version(latest, current)}
    except Exception:
        return {"current": get_current_version(), "latest": "unknown", "update_available": False}

@router.post("/install")
async def install_update(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    try:
        latest_url, download_url_template = get_urls()
        async with httpx.AsyncClient(timeout=300) as c:
            r = await c.get(latest_url)
            r.raise_for_status()
            latest = r.text.strip()
            current = get_current_version()

            if not is_newer_version(latest, current):
                return {"status": "current", "version": current}

            download_url = download_url_template.format(latest)
            r = await c.get(download_url)
            if r.status_code != 200:
                raise HTTPException(500, "Failed to download update")

            checksum_response = await c.get(f"{download_url}.sha256")
            if checksum_response.status_code != 200:
                raise HTTPException(502, "Update checksum is unavailable; refusing an unverified update")
            expected_checksum = checksum_response.text.strip().split()[0].lower()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_checksum):
                raise HTTPException(502, "Update checksum is invalid")
            actual_checksum = hashlib.sha256(r.content).hexdigest()
            if not __import__("hmac").compare_digest(actual_checksum, expected_checksum):
                raise HTTPException(502, "Update checksum verification failed")

            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_tar = os.path.join(tmpdir, "update.tar.gz")
                with open(tmp_tar, "wb") as f:
                    f.write(r.content)

                extract_dir = os.path.join(tmpdir, "extract")
                os.makedirs(extract_dir)

                with tarfile.open(tmp_tar, "r:gz") as tar:
                    safe_extract_tar(tar, extract_dir)

                payload_dir = get_payload_dir(extract_dir)
                await asyncio.to_thread(prepare_update_runtime, payload_dir)

                # Files/dirs to preserve (user data)
                skip_dirs = {"servers", "avatars", "__pycache__"}
                skip_files = {"mcpanel.db", "enderpanel.db", ".secret_key", ".data_encryption_key"}

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
                for item in os.listdir(payload_dir):
                    src = os.path.join(payload_dir, item)
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

            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(latest)

            background_tasks.add_task(restart_panel_process)
            return {"status": "restarting", "version": latest}
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
