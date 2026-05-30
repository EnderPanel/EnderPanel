import os
import time
import logging
import psutil
import threading
from collections import deque
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.server import Server
from models.panel_setting import PanelSetting
from utils.security import get_current_user
from routes.servers import dc, cname
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])
UPLOAD_LIMIT_KEY = "upload_limit_mb"
PEARLS_ENABLED_KEY = "pearls_enabled"
PEARLS_ADMIN_ONLY_UPLOAD_KEY = "pearls_admin_only_upload"
PUBLIC_DOMAIN_ENABLED_KEY = "public_domain_enabled"
PUBLIC_DOMAIN_SERVICE_URL_KEY = "public_domain_service_url"
PUBLIC_DOMAIN_BASE_DOMAIN_KEY = "public_domain_base_domain"
PUBLIC_DOMAIN_TARGET_HOST_KEY = "public_domain_target_host"
PUBLIC_DOMAIN_SERVICE_TOKEN_KEY = "public_domain_service_token"
DEFAULT_UPLOAD_LIMIT_MB = 100
MIN_UPLOAD_LIMIT_MB = 1
MAX_UPLOAD_LIMIT_MB = 2048

# In-memory history - lightweight, no DB
MAX_POINTS = 120  # 30 min at 15s intervals
history = {
    "cpu": deque(maxlen=MAX_POINTS),
    "memory": deque(maxlen=MAX_POINTS),
    "timestamps": deque(maxlen=MAX_POINTS),
}

def _collect():
    """Sample system stats every 15 seconds."""
    while True:
        try:
            history["cpu"].append(psutil.cpu_percent(interval=None))
            history["memory"].append(psutil.virtual_memory().percent)
            history["timestamps"].append(int(time.time()))
        except Exception as e:
            logger.warning("Failed to collect system stats: %s", e)
        time.sleep(15)

# Start collector thread on import
_thread = threading.Thread(target=_collect, daemon=True)
_thread.start()

def admin_only(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    return current_user


class UploadLimitUpdate(BaseModel):
    upload_limit_mb: int = Field(ge=MIN_UPLOAD_LIMIT_MB, le=MAX_UPLOAD_LIMIT_MB)


class PearlSettingsUpdate(BaseModel):
    pearls_enabled: bool
    pearls_admin_only_upload: bool


class PublicDomainSettingsUpdate(BaseModel):
    public_domain_enabled: bool
    public_domain_service_url: str = Field(default="", max_length=255)
    public_domain_base_domain: str = Field(default="", max_length=255)
    public_domain_service_token: str = Field(default="", max_length=255)


def get_upload_limit_mb(db: Session) -> int:
    setting = db.query(PanelSetting).filter(PanelSetting.key == UPLOAD_LIMIT_KEY).first()
    if not setting:
        setting = PanelSetting(key=UPLOAD_LIMIT_KEY, value=str(DEFAULT_UPLOAD_LIMIT_MB))
        db.add(setting)
        db.commit()
        db.refresh(setting)
    try:
        return max(MIN_UPLOAD_LIMIT_MB, min(MAX_UPLOAD_LIMIT_MB, int(setting.value)))
    except (TypeError, ValueError):
        setting.value = str(DEFAULT_UPLOAD_LIMIT_MB)
        db.commit()
        return DEFAULT_UPLOAD_LIMIT_MB


def get_bool_panel_setting(db: Session, key: str, default: bool) -> bool:
    setting = db.query(PanelSetting).filter(PanelSetting.key == key).first()
    if not setting:
        setting = PanelSetting(key=key, value="1" if default else "0")
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return str(setting.value).strip().lower() in {"1", "true", "yes", "on"}


def get_text_panel_setting(db: Session, key: str, default: str = "") -> str:
    setting = db.query(PanelSetting).filter(PanelSetting.key == key).first()
    if not setting:
        setting = PanelSetting(key=key, value=default)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return str(setting.value or "").strip()

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    servers = db.query(Server).all()

    server_list = []
    for s in servers:
        status = "stopped"
        try:
            c = dc().containers.get(cname(s.id))
            status = c.status
        except Exception as e:
            logger.debug("Could not get container status for server %s: %s", s.id, e)
        server_list.append({
            "id": s.id, "name": s.name, "type": s.server_type,
            "version": s.version, "port": s.port, "status": status
        })

    # Non-blocking current sample for the headline card.
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    # psutil's "used" field can be platform-specific, especially on macOS.
    # Derive usage from total - available so the bar and text stay consistent.
    mem_used = max(0, memory.total - memory.available)
    mem_percent = round((mem_used / memory.total) * 100, 1) if memory.total else 0
    disk = psutil.disk_usage(os.path.abspath(os.sep))

    docker_available = True
    try:
        containers = dc().containers.list(all=True)
        docker_running = len([c for c in containers if c.status == "running"])
        docker_total = len(containers)
    except Exception as e:
        logger.warning("Could not list Docker containers: %s", e)
        docker_running = 0
        docker_total = 0
        docker_available = False

    # Additional stats: network and uptime
    try:
        net_io = psutil.net_io_counters()
        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
    except Exception as e:
        logger.warning("Could not read network I/O counters: %s", e)
        bytes_sent = 0
        bytes_recv = 0

    try:
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)
    except Exception as e:
        logger.warning("Could not read boot time: %s", e)
        uptime_seconds = 0

    current_ts = int(time.time())
    cpu_history = list(history["cpu"])
    memory_history = list(history["memory"])
    timestamp_history = list(history["timestamps"])

    should_append_current = not timestamp_history or timestamp_history[-1] != current_ts
    if should_append_current:
        cpu_history.append(cpu_percent)
        memory_history.append(mem_percent)
        timestamp_history.append(current_ts)

    cpu_history = cpu_history[-MAX_POINTS:]
    memory_history = memory_history[-MAX_POINTS:]
    timestamp_history = timestamp_history[-MAX_POINTS:]

    return {
        "servers": server_list,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_total": memory.total,
            "memory_used": mem_used,
            "memory_percent": mem_percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent,
            "net_sent": bytes_sent,
            "net_recv": bytes_recv,
            "uptime_seconds": uptime_seconds
        },
        "docker": {"running": docker_running, "total": docker_total, "available": docker_available},
        "counts": {"servers": len(servers), "users": db.query(User).count()},
        "history": {
            "cpu": cpu_history,
            "memory": memory_history,
            "timestamps": timestamp_history,
        }
    }


@router.get("/panel-settings")
def get_panel_settings(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    upload_limit_mb = get_upload_limit_mb(db)
    return {
        "upload_limit_mb": upload_limit_mb,
        "upload_limit_bytes": upload_limit_mb * 1024 * 1024,
        "min_upload_limit_mb": MIN_UPLOAD_LIMIT_MB,
        "max_upload_limit_mb": MAX_UPLOAD_LIMIT_MB,
        "pearls_enabled": get_bool_panel_setting(db, PEARLS_ENABLED_KEY, True),
        "pearls_admin_only_upload": get_bool_panel_setting(db, PEARLS_ADMIN_ONLY_UPLOAD_KEY, False),
        "public_domain_enabled": get_bool_panel_setting(db, PUBLIC_DOMAIN_ENABLED_KEY, False),
        "public_domain_service_url": get_text_panel_setting(db, PUBLIC_DOMAIN_SERVICE_URL_KEY, "https://vercel-playit-api.vercel.app/api/cloudflare"),
        "public_domain_base_domain": get_text_panel_setting(db, PUBLIC_DOMAIN_BASE_DOMAIN_KEY, ""),
        "public_domain_service_token": get_text_panel_setting(db, PUBLIC_DOMAIN_SERVICE_TOKEN_KEY, ""),
    }


@router.put("/panel-settings/upload-limit")
def update_upload_limit(
    payload: UploadLimitUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    setting = db.query(PanelSetting).filter(PanelSetting.key == UPLOAD_LIMIT_KEY).first()
    if not setting:
        setting = PanelSetting(key=UPLOAD_LIMIT_KEY, value=str(payload.upload_limit_mb))
        db.add(setting)
    else:
        setting.value = str(payload.upload_limit_mb)
    db.commit()
    return {
        "status": "updated",
        "upload_limit_mb": payload.upload_limit_mb,
        "upload_limit_bytes": payload.upload_limit_mb * 1024 * 1024,
    }


@router.put("/panel-settings/pearls")
def update_pearl_settings(
    payload: PearlSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    for key, enabled in (
        (PEARLS_ENABLED_KEY, payload.pearls_enabled),
        (PEARLS_ADMIN_ONLY_UPLOAD_KEY, payload.pearls_admin_only_upload),
    ):
        setting = db.query(PanelSetting).filter(PanelSetting.key == key).first()
        if not setting:
            setting = PanelSetting(key=key, value="1" if enabled else "0")
            db.add(setting)
        else:
            setting.value = "1" if enabled else "0"
    db.commit()
    return {
        "status": "updated",
        "pearls_enabled": payload.pearls_enabled,
        "pearls_admin_only_upload": payload.pearls_admin_only_upload,
    }


@router.put("/panel-settings/public-domain")
def update_public_domain_settings(
    payload: PublicDomainSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    values = {
        PUBLIC_DOMAIN_ENABLED_KEY: "1" if payload.public_domain_enabled else "0",
        PUBLIC_DOMAIN_SERVICE_URL_KEY: payload.public_domain_service_url.strip(),
        PUBLIC_DOMAIN_BASE_DOMAIN_KEY: payload.public_domain_base_domain.strip().lower().rstrip("."),
        PUBLIC_DOMAIN_SERVICE_TOKEN_KEY: payload.public_domain_service_token.strip(),
    }

    for key, value in values.items():
        setting = db.query(PanelSetting).filter(PanelSetting.key == key).first()
        if not setting:
            setting = PanelSetting(key=key, value=value)
            db.add(setting)
        else:
            setting.value = value

    db.commit()
    return {
        "status": "updated",
        "public_domain_enabled": payload.public_domain_enabled,
        "public_domain_service_url": values[PUBLIC_DOMAIN_SERVICE_URL_KEY],
        "public_domain_base_domain": values[PUBLIC_DOMAIN_BASE_DOMAIN_KEY],
        "public_domain_service_token": values[PUBLIC_DOMAIN_SERVICE_TOKEN_KEY],
    }
