import os
import re
import httpx
import asyncio
import shutil
import docker
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import SERVERS_DIR

router = APIRouter(prefix="/api/servers", tags=["servers"])

IMAGE = "mc-panel-server"
PREFIX = "mc-panel"

def sanitize(n: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', n)

def sdir(sid: int, name: str) -> str:
    return os.path.join(SERVERS_DIR, f"{sid}-{sanitize(name)}")

def cname(sid: int) -> str:
    return f"{PREFIX}-{sid}"

def dc():
    return docker.from_env()

def java_cmd(version: str) -> str:
    return "/opt/java/openjdk/bin/java"

def to_dict(s: Server) -> dict:
    return {
        "id": s.id, "name": s.name, "status": s.status, "server_type": s.server_type,
        "port": s.port, "max_players": s.max_players, "version": s.version, "motd": s.motd,
        "ram_min": s.ram_min, "ram_max": s.ram_max, "cpu_cores": s.cpu_cores,
        "custom_launch_command": s.custom_launch_command,
        "avatar": f"/api/avatars/{s.avatar}" if s.avatar else None
    }

def get_status(sid: int) -> str:
    try:
        c = dc().containers.get(cname(sid))
        return "running" if c.status == "running" else "stopped"
    except docker.errors.NotFound:
        return "stopped"
    except:
        return "stopped"

class Create(BaseModel):
    name: str
    server_type: str = "paper"
    port: int = 25565
    max_players: int = 20
    version: str = "1.21.11"
    motd: str = "A Minecraft Server"
    ram_min: int = 512
    ram_max: int = 1024
    cpu_cores: int = 1
    custom_launch_command: Optional[str] = None

async def download_jar(stype: str, ver: str, path: str) -> bool:
    jar = os.path.join(path, "server.jar")
    try:
        async with httpx.AsyncClient(timeout=300) as c:
            if stype == "paper":
                r = await c.get(f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds")
                b = r.json().get("builds", [])
                if not b: return False
                n = b[-1]["downloads"]["application"]["name"]
                r = await c.get(f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds/{b[-1]['build']}/downloads/{n}")
                with open(jar, "wb") as f: f.write(r.content)
                return True
            elif stype == "vanilla":
                r = await c.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
                for v in r.json()["versions"]:
                    if v["id"] == ver:
                        r = await c.get(v["url"])
                        r = await c.get(r.json()["downloads"]["server"]["url"])
                        with open(jar, "wb") as f: f.write(r.content)
                        return True
                return False
            elif stype == "fabric":
                r = await c.get(f"https://meta.fabricmc.net/v2/versions/loader/{ver}")
                l = r.json()
                if not l: return False
                r = await c.get("https://meta.fabricmc.net/v2/versions/installer")
                i = r.json()
                if not i: return False
                url = f"https://meta.fabricmc.net/v2/versions/loader/{ver}/{l[0]['loader']['version']}/{i[0]['version']}/server/jar"
                r = await c.get(url)
                with open(jar, "wb") as f: f.write(r.content)
                return True
            elif stype == "neoforge":
                r = await c.get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.json")
                p = ver.replace("1.", "")
                m = [v for v in r.json()["versions"] if v.startswith(p) and "alpha" not in v and "beta" not in v]
                if not m: return False
                r = await c.get(f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{m[-1]}/neoforge-{m[-1]}-installer.jar")
                with open(jar, "wb") as f: f.write(r.content)
                return True
            elif stype == "forge":
                for s in ["recommended", "latest"]:
                    r = await c.get(f"https://maven.minecraftforge.net/net/minecraftforge/forge/{ver}-{s}/forge-{ver}-{s}-installer.jar")
                    if r.status_code == 200:
                        tmp = os.path.join(path, "forge.jar")
                        with open(tmp, "wb") as f: f.write(r.content)
                        proc = await asyncio.create_subprocess_exec("java", "-jar", "forge.jar", "--installServer", cwd=path)
                        await proc.wait()
                        os.remove(tmp)
                        return proc.returncode == 0
                return False
    except Exception as e:
        print(f"Download error: {e}")
        return False

@router.get("/")
def list_servers(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    servers = db.query(Server).filter(Server.owner_id == user.id).all()
    for s in servers:
        s.status = get_status(s.id)
    db.commit()
    return [to_dict(s) for s in servers]

@router.get("/{sid}")
def get_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    s.status = get_status(sid)
    db.commit()
    return to_dict(s)

@router.post("/")
async def create_server(data: Create, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(Server).filter(Server.port == data.port).first():
        raise HTTPException(400, "Port in use")
    s = Server(name=data.name, owner_id=user.id, server_type=data.server_type, port=data.port,
        max_players=data.max_players, version=data.version, motd=data.motd, ram_min=data.ram_min,
        ram_max=data.ram_max, cpu_cores=data.cpu_cores, custom_launch_command=data.custom_launch_command)
    db.add(s); db.commit(); db.refresh(s)
    d = sdir(s.id, s.name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "eula.txt"), "w") as f: f.write("eula=true\n")
    with open(os.path.join(d, "server.properties"), "w") as f:
        f.write(f"server-port=25565\nmax-players={data.max_players}\nmotd={data.motd}\n")
        f.write("enable-rcon=true\nrcon.port=25575\nrcon.password=mcpanel\n")
    ok = await download_jar(data.server_type, data.version, d)
    try: dc().images.get(f"{IMAGE}:latest")
    except:
        try: dc().images.build(path=os.path.dirname(os.path.dirname(__file__)), tag=f"{IMAGE}:latest", dockerfile="Dockerfile")
        except: pass
    r = to_dict(s); r["jar_downloaded"] = ok
    return r

@router.post("/{sid}/start")
def start_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    client = dc()
    name = cname(sid)
    
    try:
        c = client.containers.get(name)
        if c.status == "running":
            raise HTTPException(400, "Already running")
        c.start()
        s.status = "running"
        db.commit()
        return {"status": "started"}
    except docker.errors.NotFound:
        pass
    except HTTPException:
        raise
    
    d = sdir(sid, s.name)
    if not os.path.exists(os.path.join(d, "server.jar")):
        raise HTTPException(400, "No server.jar")
    
    java = java_cmd(s.version)
    if s.custom_launch_command:
        cmd = s.custom_launch_command.replace("{jar}", "server.jar").replace("{ram_min}", str(s.ram_min))
        cmd = cmd.replace("{ram_max}", str(s.ram_max)).replace("{java}", java).split()
    else:
        cmd = [java, f"-Xmx{s.ram_max}M", f"-Xms{s.ram_min}M", "-jar", "server.jar", "nogui"]
    
    client.containers.run(
        f"{IMAGE}:latest",
        command=cmd,
        name=name,
        detach=True,
        tty=True,
        stdin_open=True,
        volumes={d: {"bind": "/server", "mode": "rw"}},
        ports={"25565/tcp": s.port, "25575/tcp": 25575 + s.id},
        mem_limit=f"{s.ram_max}m",
        memswap_limit=f"{s.ram_max}m",
        cpu_period=100000,
        cpu_quota=int(s.cpu_cores * 100000),
        working_dir="/server",
        environment={"EULA": "TRUE"}
    )
    
    s.status = "running"
    db.commit()
    return {"status": "started"}

@router.post("/{sid}/stop")
def stop_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        c = dc().containers.get(cname(sid))
        c.kill()
    except docker.errors.NotFound:
        pass
    except Exception as e:
        print(f"Stop error: {e}")
    
    s.status = "stopped"
    db.commit()
    return {"status": "stopped"}

@router.post("/{sid}/restart")
def restart_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stop_server(sid, db, user)
    return start_server(sid, db, user)

@router.delete("/{sid}")
def delete_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        c = dc().containers.get(cname(sid))
        c.kill()
        c.remove(force=True)
    except: pass
    
    d = sdir(sid, s.name)
    if os.path.exists(d):
        shutil.rmtree(d)
    
    db.delete(s)
    db.commit()
    return {"status": "deleted"}
