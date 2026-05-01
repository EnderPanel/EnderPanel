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
from utils.security import get_current_user
from routes.servers import dc, cname

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

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

    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    mem_used = memory.total - memory.available
    mem_percent = round(100 - (memory.available / memory.total) * 100, 1)
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

    return {
        "servers": server_list,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
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
            "cpu": list(history["cpu"]),
            "memory": list(history["memory"]),
            "timestamps": list(history["timestamps"])
        }
    }
