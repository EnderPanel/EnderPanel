import os
import re
import httpx
import asyncio
import shutil
import docker
from docker.errors import NotFound as DockerNotFound
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
        "avatar": f"/api/avatars/{s.avatar}" if s.avatar else None  # type: ignore[union-attr]
    }

def get_status(sid: int) -> str:
    try:
        c = dc().containers.get(cname(sid))
        return "running" if c.status == "running" else "stopped"
    except DockerNotFound:
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

async def download_jar(stype: str, ver: str, path: str) -> bool:  # type: ignore[return]
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
                try:
                    p = ver[2:]
                    p_dot = p + "."
                    r = await c.get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml")
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(r.text)
                    versions = [v.text for v in root.findall(".//version") if v.text and v.text.startswith(p_dot)]
                    if not versions:
                        return False

                    neoforge_ver = versions[-1]
                    installer_url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_ver}/neoforge-{neoforge_ver}-installer.jar"
                    r = await c.get(installer_url)

                    if r.status_code != 200:
                        return False

                    tmp = os.path.join(path, "neoforge-installer.jar")
                    with open(tmp, "wb") as f: f.write(r.content)
                    proc = await asyncio.create_subprocess_exec(
                        "docker", "run", "--rm", "-v", f"{path}:/server", "-w", "/server",
                        "mc-panel-server:latest", "/opt/java/openjdk/bin/java",
                        "-jar", "neoforge-installer.jar", "--installServer", "--server.jar",
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    await proc.communicate()
                    os.remove(tmp)

                    if os.path.exists(os.path.join(path, "server.jar")):
                        return True
                except Exception as e:
                    print(f"NeoForge download error: {e}")
                    return False
            elif stype == "forge":
                try:
                    r = await c.get(f"https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml")
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(r.text)
                    versions = root.findall(".//version")
                    matching = [v.text for v in versions if v.text and v.text.startswith(ver)]
                    if not matching:
                        return False
                    
                    forge_ver = matching[-1]
                    installer_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_ver}/forge-{forge_ver}-installer.jar"
                    r = await c.get(installer_url)
                    
                    if r.status_code != 200:
                        return False
                        
                    tmp = os.path.join(path, "forge-installer.jar")
                    with open(tmp, "wb") as f: f.write(r.content)
                    proc = await asyncio.create_subprocess_exec(
                        "docker", "run", "--rm", "-v", f"{path}:/server", "-w", "/server",
                        "mc-panel-server:latest", "/opt/java/openjdk/bin/java",
                        "-jar", "forge-installer.jar", "--installServer",
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    await proc.communicate()
                    os.remove(tmp)
                    
                    if os.path.exists(os.path.join(path, "libraries")):
                        return True
                    return False
                except Exception as e:
                    print(f"Forge download error: {e}")
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
    port = data.port
    while db.query(Server).filter(Server.port == port).first():
        port += 1
    port_changed = port != data.port
    s = Server(name=data.name, owner_id=user.id, server_type=data.server_type, port=port,
        max_players=data.max_players, version=data.version, motd=data.motd, ram_min=data.ram_min,
        ram_max=data.ram_max, cpu_cores=data.cpu_cores, custom_launch_command=data.custom_launch_command)
    db.add(s); db.commit(); db.refresh(s)
    d = sdir(s.id, s.name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "eula.txt"), "w") as f: f.write("eula=true\n")
    with open(os.path.join(d, "server.properties"), "w") as f:
        f.write(f"server-port={port}\nmax-players={data.max_players}\nmotd={data.motd}\n")
        f.write("enable-rcon=true\nrcon.port=25575\nrcon.password=mcpanel\n")
    ok = await download_jar(data.server_type, data.version, d)
    try: dc().images.get(f"{IMAGE}:latest")
    except:
        try: dc().images.build(path=os.path.dirname(os.path.dirname(__file__)), tag=f"{IMAGE}:latest", dockerfile="Dockerfile")
        except: pass
    r = to_dict(s); r["jar_downloaded"] = ok
    if port_changed:
        r["port_changed"] = True
        r["original_port"] = data.port
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
    except DockerNotFound:
        pass
    except HTTPException:
        raise
    
    d = sdir(sid, s.name)
    
    java = java_cmd(s.version)
    if s.custom_launch_command:
        cmd = s.custom_launch_command.replace("{jar}", "server.jar").replace("{ram_min}", str(s.ram_min))
        cmd = cmd.replace("{ram_max}", str(s.ram_max)).replace("{java}", java).split()
    else:
        unix_args = None
        ua_root = os.path.join(d, "unix_args.txt")
        if os.path.exists(ua_root):
            unix_args = ua_root
        else:
            for root_dir, dirs, files in os.walk(d):
                if "unix_args.txt" in files and root_dir != d:
                    unix_args = os.path.join(root_dir, "unix_args.txt")
                    break

        server_jar = os.path.join(d, "server.jar")
        has_server_jar = os.path.exists(server_jar) and os.path.getsize(server_jar) > 50000

        if has_server_jar and unix_args:
            with open(os.path.join(d, "user_jvm_args.txt"), "w") as f:
                f.write(f"-Xmx{s.ram_max}M\n-Xms{s.ram_min}M\n-XX:+UseG1GC\n")
            ua_rel = os.path.relpath(unix_args, d)
            cmd = [java, "@user_jvm_args.txt", f"@{ua_rel}", "-jar", "server.jar", "nogui"]
        elif has_server_jar:
            cmd = [java, f"-Xmx{s.ram_max}M", f"-Xms{s.ram_min}M", "-jar", "server.jar", "nogui"]
        elif unix_args:
            with open(os.path.join(d, "user_jvm_args.txt"), "w") as f:
                f.write(f"-Xmx{s.ram_max}M\n-Xms{s.ram_min}M\n-XX:+UseG1GC\n")
            ua_rel = os.path.relpath(unix_args, d)
            cmd = [java, "@user_jvm_args.txt", f"@{ua_rel}", "nogui"]
        else:
            raise HTTPException(400, "No server files found")
    
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
    except DockerNotFound:
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
