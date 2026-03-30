import os
import psutil
import docker
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from routes.servers import dc, cname, to_dict

router = APIRouter(prefix="/api/admin", tags=["admin"])

def admin_only(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    return current_user

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _: User = Depends(admin_only)):
    servers = db.query(Server).all()
    users = db.query(User).all()

    # Server statuses from Docker
    server_list = []
    for s in servers:
        status = "stopped"
        try:
            c = dc().containers.get(cname(s.id))
            status = c.status
        except:
            pass
        server_list.append({
            "id": s.id,
            "name": s.name,
            "type": s.server_type,
            "version": s.version,
            "port": s.port,
            "status": status,
            "owner": s.owner_id
        })

    # System stats
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # Docker info
    try:
        containers = dc().containers.list(all=True)
        docker_running = len([c for c in containers if c.status == "running"])
        docker_total = len(containers)
    except:
        docker_running = 0
        docker_total = 0

    return {
        "servers": server_list,
        "users": [{"id": u.id, "username": u.username, "email": u.email, "is_admin": u.is_admin} for u in users],
        "system": {
            "cpu_percent": cpu_percent,
            "memory_total": memory.total,
            "memory_used": memory.used,
            "memory_percent": memory.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_percent": disk.percent
        },
        "docker": {
            "running": docker_running,
            "total": docker_total
        },
        "counts": {
            "servers": len(servers),
            "users": len(users)
        }
    }

@router.get("/system")
def get_system(_: User = Depends(admin_only)):
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": cpu_percent,
        "memory_total": memory.total,
        "memory_used": memory.used,
        "memory_percent": memory.percent,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_percent": disk.percent
    }
