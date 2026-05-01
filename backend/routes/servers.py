import os
import re
import logging
import httpx
import asyncio
import shutil
import docker
from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import SERVERS_DIR
from .playit_runtime import ensure_playit_tunnel, start_playit_container, stop_playit_container
from utils.docker_client import get_docker_client

router = APIRouter(prefix="/api/servers", tags=["servers"])
logger = logging.getLogger(__name__)

IMAGE = "mc-panel-server"
PREFIX = "mc-panel"
FALLBACK_VERSIONS = {
    "paper": ["1.21.11", "1.21.10", "1.21.8", "1.20.6"],
    "vanilla": ["1.21.11", "1.21.10", "1.21.8", "1.20.6"],
    "fabric": ["1.21.11", "1.21.10", "1.21.8", "1.20.6"],
    "forge": ["1.21.1", "1.20.1", "1.19.2"],
    "neoforge": ["1.21.1", "1.20.6"],
}
ALLOWED_SERVER_TYPES = set(FALLBACK_VERSIONS)
MIN_SERVER_PORT = 1024
MAX_SERVER_PORT = 65535
MAX_RAM_MB = 65536
MAX_SWAP_MB = 65536
MAX_CPU_CORES = 64

def sanitize(n: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', n)

def sdir(sid: int, name: str) -> str:
    return os.path.join(SERVERS_DIR, f"{sid}-{sanitize(name)}")

def cname(sid: int) -> str:
    return f"{PREFIX}-{sid}"

def dc():
    return get_docker_client()


def eula_file(sid: int, name: str) -> str:
    return os.path.join(sdir(sid, name), "eula.txt")


def has_accepted_eula(sid: int, name: str) -> bool:
    path = eula_file(sid, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return "eula=true" in f.read().lower()
    return False

def java_version_for_mc(mc_version: str) -> int:
    try:
        parts = mc_version.split(".")
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return 21
    if minor > 20 or (minor == 20 and patch >= 5):
        return 21
    if minor >= 17:
        return 17
    return 11


def image_for_mc(mc_version: str) -> str:
    v = java_version_for_mc(mc_version)
    if v == 11:
        return f"{IMAGE}:java11"
    if v == 17:
        return f"{IMAGE}:java17"
    return f"{IMAGE}:latest"


def java_cmd(version: str) -> str:
    return "/opt/java/openjdk/bin/java"


def server_properties_file(sid: int, name: str) -> str:
    return os.path.join(sdir(sid, name), "server.properties")


def ensure_server_properties(sid: int, name: str, port: int, max_players: int, motd: str) -> None:
    path = server_properties_file(sid, name)
    existing: dict[str, str] = {}

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                existing[key] = value

    existing["server-port"] = str(port)
    existing["max-players"] = str(max_players)
    existing["motd"] = motd
    existing["enable-rcon"] = "false"
    existing["broadcast-rcon-to-ops"] = "false"
    existing["rcon.port"] = "25575"
    existing["rcon.password"] = ""

    with open(path, "w", encoding="utf-8") as f:
        f.write("#Minecraft server properties\n")
        for key, value in existing.items():
            f.write(f"{key}={value}\n")

def to_dict(s: Server) -> dict:
    return {
        "id": s.id, "name": s.name, "status": s.status, "server_type": s.server_type,
        "port": s.port, "max_players": s.max_players, "version": s.version, "motd": s.motd,
        "ram_min": s.ram_min, "ram_max": s.ram_max, "swap_mb": s.swap_mb, "cpu_cores": s.cpu_cores,
        "custom_launch_command": s.custom_launch_command,
        "avatar": f"/api/avatars/{s.avatar}" if s.avatar else None,  # type: ignore[union-attr]
        "eula_accepted": has_accepted_eula(s.id, s.name),
        "container_started_at": get_container_started_at(s.id),
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "playit_enabled": s.playit_enabled,
        "playit_domain": s.playit_domain,
        "playit_tunnel_id": s.playit_tunnel_id,
    }

def get_status(sid: int) -> str:
    try:
        c = dc().containers.get(cname(sid))
        return "running" if c.status == "running" else "stopped"
    except DockerNotFound:
        return "stopped"
    except:
        return "stopped"


def get_container_started_at(sid: int) -> str | None:
    try:
        c = dc().containers.get(cname(sid))
        started_at = (c.attrs.get("State") or {}).get("StartedAt")
        return started_at if isinstance(started_at, str) and started_at else None
    except DockerNotFound:
        return None
    except Exception:
        return None

class Create(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    server_type: str = "paper"
    port: int = Field(default=25565, ge=MIN_SERVER_PORT, le=MAX_SERVER_PORT)
    max_players: int = Field(default=20, ge=1, le=1000)
    version: str = Field(default="1.21.11", min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._+\-]+$")
    motd: str = Field(default="A Minecraft Server", max_length=255)
    ram_min: int = Field(default=512, ge=256, le=MAX_RAM_MB)
    ram_max: int = Field(default=1024, ge=256, le=MAX_RAM_MB)
    swap_mb: int = Field(default=512, ge=0, le=MAX_SWAP_MB)
    cpu_cores: int = Field(default=1, ge=1, le=MAX_CPU_CORES)
    custom_launch_command: Optional[str] = Field(default=None, max_length=2048)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not sanitize(value).strip("_"):
            raise ValueError("Server name must contain letters, numbers, hyphens, or underscores")
        return value

    @field_validator("server_type")
    @classmethod
    def validate_server_type(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_SERVER_TYPES:
            raise ValueError("Unsupported server type")
        return normalized

    @model_validator(mode="after")
    def validate_memory(self):
        if self.ram_min > self.ram_max:
            raise ValueError("Minimum RAM cannot be greater than maximum RAM")
        return self

async def download_jar(stype: str, ver: str, path: str) -> tuple[bool, str | None]:
    jar = os.path.join(path, "server.jar")
    try:
        async with httpx.AsyncClient(timeout=300) as c:
            if stype == "paper":
                r = await c.get(f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds")
                b = r.json().get("builds", [])
                if not b: return False, f"No Paper builds found for {ver}."
                n = b[-1]["downloads"]["application"]["name"]
                r = await c.get(f"https://api.papermc.io/v2/projects/paper/versions/{ver}/builds/{b[-1]['build']}/downloads/{n}")
                with open(jar, "wb") as f: f.write(r.content)
                return True, None
            elif stype == "vanilla":
                r = await c.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
                for v in r.json()["versions"]:
                    if v["id"] == ver:
                        r = await c.get(v["url"])
                        r = await c.get(r.json()["downloads"]["server"]["url"])
                        with open(jar, "wb") as f: f.write(r.content)
                        return True, None
                return False, f"Vanilla version {ver} was not found."
            elif stype == "fabric":
                r = await c.get(f"https://meta.fabricmc.net/v2/versions/loader/{ver}")
                l = r.json()
                if not l: return False, f"No Fabric loader found for {ver}."
                r = await c.get("https://meta.fabricmc.net/v2/versions/installer")
                i = r.json()
                if not i: return False, "No Fabric installer versions were returned."
                url = f"https://meta.fabricmc.net/v2/versions/loader/{ver}/{l[0]['loader']['version']}/{i[0]['version']}/server/jar"
                r = await c.get(url)
                with open(jar, "wb") as f: f.write(r.content)
                return True, None
            elif stype == "neoforge":
                try:
                    p = ver[2:]
                    p_dot = p + "."
                    r = await c.get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml")
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(r.text)
                    versions = [v.text for v in root.findall(".//version") if v.text and v.text.startswith(p_dot)]
                    if not versions:
                        return False, f"No NeoForge builds found for {ver}."

                    neoforge_ver = versions[-1]
                    installer_url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{neoforge_ver}/neoforge-{neoforge_ver}-installer.jar"
                    r = await c.get(installer_url)

                    if r.status_code != 200:
                        return False, f"NeoForge installer download failed with status {r.status_code}."

                    tmp = os.path.join(path, "neoforge-installer.jar")
                    with open(tmp, "wb") as f: f.write(r.content)
                    proc = await asyncio.create_subprocess_exec(
                        "docker", "run", "--rm", "-v", f"{path}:/server", "-w", "/server",
                        image_for_mc(ver), "/opt/java/openjdk/bin/java",
                        "-jar", "neoforge-installer.jar", "--installServer", "--server.jar",
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    await proc.communicate()
                    os.remove(tmp)

                    if os.path.exists(os.path.join(path, "server.jar")):
                        return True, None
                except Exception as e:
                    print(f"NeoForge download error: {e}")
                    return False, f"NeoForge download error: {e}"
            elif stype == "forge":
                try:
                    r = await c.get(f"https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml")
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(r.text)
                    versions = root.findall(".//version")
                    matching = [v.text for v in versions if v.text and v.text.startswith(ver)]
                    if not matching:
                        return False, f"No Forge builds found for {ver}."
                    
                    forge_ver = matching[-1]
                    installer_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_ver}/forge-{forge_ver}-installer.jar"
                    r = await c.get(installer_url)
                    
                    if r.status_code != 200:
                        return False, f"Forge installer download failed with status {r.status_code}."
                        
                    tmp = os.path.join(path, "forge-installer.jar")
                    with open(tmp, "wb") as f: f.write(r.content)
                    proc = await asyncio.create_subprocess_exec(
                        "docker", "run", "--rm", "-v", f"{path}:/server", "-w", "/server",
                        image_for_mc(ver), "/opt/java/openjdk/bin/java",
                        "-jar", "forge-installer.jar", "--installServer",
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                    await proc.communicate()
                    os.remove(tmp)
                    
                    if os.path.exists(os.path.join(path, "libraries")):
                        return True, None
                    return False, "Forge installer completed, but expected libraries were not created."
                except Exception as e:
                    print(f"Forge download error: {e}")
                    return False, f"Forge download error: {e}"
    except Exception as e:
        print(f"Download error: {e}")
        return False, f"Download error: {e}"

    return False, f"Unsupported server type or installer failed for {stype} {ver}."

@router.get("/versions/{server_type}")
async def get_versions(server_type: str):
    server_type = server_type.strip().lower()
    if server_type not in ALLOWED_SERVER_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported server type")

    versions = []
    fallback_used = False
    detail = None
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            if server_type == "paper":
                r = await c.get("https://api.papermc.io/v2/projects/paper")
                data = r.json()
                versions = data.get("versions", [])
                versions.reverse()
            elif server_type == "vanilla":
                r = await c.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json")
                data = r.json()
                versions = [v["id"] for v in data.get("versions", []) if v.get("type") == "release"]
            elif server_type == "fabric":
                r = await c.get("https://meta.fabricmc.net/v2/versions/game")
                data = r.json()
                versions = [v["version"] for v in data if v.get("stable")]
            elif server_type == "forge":
                r = await c.get("https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml")
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                all_versions = [v.text for v in root.findall(".//version") if v.text]
                seen = set()
                for v in all_versions:
                    mc_ver = v.rsplit("-", 1)[0] if "-" in v else v
                    if mc_ver not in seen:
                        seen.add(mc_ver)
                        versions.append(mc_ver)
                versions.reverse()
            elif server_type == "neoforge":
                r = await c.get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml")
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                all_versions = [v.text for v in root.findall(".//version") if v.text]
                seen = set()
                for v in all_versions:
                    parts = v.split(".")
                    if len(parts) >= 2:
                        mc_ver = f"1.{parts[0]}.{parts[1]}"
                        if mc_ver not in seen:
                            seen.add(mc_ver)
                            versions.append(mc_ver)
                versions.reverse()
    except Exception as e:
        print(f"Error fetching {server_type} versions: {e}")
        detail = str(e)

    if not versions:
        versions = FALLBACK_VERSIONS.get(server_type, [])
        fallback_used = bool(versions)

    return {
        "server_type": server_type,
        "versions": versions,
        "fallback_used": fallback_used,
        "detail": detail,
    }

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
        if port > MAX_SERVER_PORT:
            raise HTTPException(status_code=400, detail="No available server ports")
    port_changed = port != data.port
    s = Server(name=data.name, owner_id=user.id, server_type=data.server_type, port=port,
        max_players=data.max_players, version=data.version, motd=data.motd, ram_min=data.ram_min,
        ram_max=data.ram_max, swap_mb=data.swap_mb, cpu_cores=data.cpu_cores,
        custom_launch_command=data.custom_launch_command)
    db.add(s); db.commit(); db.refresh(s)
    d = sdir(s.id, s.name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "eula.txt"), "w", encoding="utf-8") as f:
        f.write("eula=false\n")
    ensure_server_properties(s.id, s.name, port, data.max_players, data.motd)
    ok, download_error = await download_jar(data.server_type, data.version, d)
    try:
        client = dc()
        base = os.path.dirname(os.path.dirname(__file__))
        for tag, dockerfile in [("latest", "Dockerfile"), ("java17", "Dockerfile.java17"), ("java11", "Dockerfile.java11")]:
            try: client.images.get(f"{IMAGE}:{tag}")
            except:
                try: client.images.build(path=base, tag=f"{IMAGE}:{tag}", dockerfile=dockerfile)
                except Exception as e:
                    logger.warning(f"Could not build Docker image {tag}: {e}")
    except Exception as e:
        if "Permission denied" in str(e):
            logger.warning("Docker permission denied - user may not be in docker group")
        else:
            logger.warning(f"Could not access Docker: {e}")
    r = to_dict(s); r["jar_downloaded"] = ok; r["download_error"] = download_error
    if port_changed:
        r["port_changed"] = True
        r["original_port"] = data.port
    return r

class StartServerRequest(BaseModel):
    accept_eula: bool = False


def write_eula_accept(sid: int, name: str) -> None:
    path = eula_file(sid, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("eula=true\n")


@router.post("/{sid}/start")
async def start_server(
    sid: int,
    data: Optional[StartServerRequest] = Body(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        client = dc()
    except Exception as e:
        if "Permission denied" in str(e):
            raise HTTPException(500, "Docker permission denied. Ensure your user is in the docker group and has logged out/back in.")
        raise HTTPException(500, f"Cannot connect to Docker: {str(e)}")
    
    name = cname(sid)
    
    # Remove existing container if it uses the wrong Java image
    try:
        c = client.containers.get(name)
        if c.status == "running":
            raise HTTPException(400, "Already running")
        correct_image = image_for_mc(s.version)
        container_image = (c.image.tags or [""])[0]
        if correct_image != container_image:
            c.remove(force=True)
        else:
            if not has_accepted_eula(sid, s.name):
                if data and data.accept_eula:
                    write_eula_accept(sid, s.name)
                else:
                    raise HTTPException(400, "EULA acceptance required")
            c.start()
            s.status = "running"
            db.commit()
            if s.playit_enabled and user.playit_agent_secret:
                try:
                    start_playit_container(s.id, user.playit_agent_secret)
                    tunnel_id, domain, detail = ensure_playit_tunnel(s, user)
                    if tunnel_id:
                        s.playit_tunnel_id = tunnel_id
                        s.playit_domain = domain
                        db.commit()
                    elif detail:
                        logger.warning("Playit tunnel failed for server %s: %s", s.id, detail)
                except Exception as exc:
                    logger.warning("Playit agent failed for server %s: %s", s.id, exc)
            return {"status": "started"}
    except DockerNotFound:
        pass
    except HTTPException:
        raise
    
    d = sdir(sid, s.name)
    ensure_server_properties(sid, s.name, s.port, s.max_players, s.motd)

    # Ensure the correct image is built
    base = os.path.dirname(os.path.dirname(__file__))
    for tag, dockerfile in [("latest", "Dockerfile"), ("java17", "Dockerfile.java17"), ("java11", "Dockerfile.java11")]:
        try: client.images.get(f"{IMAGE}:{tag}")
        except:
            try: client.images.build(path=base, tag=f"{IMAGE}:{tag}", dockerfile=dockerfile)
            except Exception as e:
                logger.warning(f"Could not build Docker image {tag}: {e}")

    if not has_accepted_eula(sid, s.name):
        if data and data.accept_eula:
            write_eula_accept(sid, s.name)
        else:
            raise HTTPException(400, "EULA acceptance required")
    
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

    # Always clean up any leftover container before creating
    try:
        client.containers.get(name).remove(force=True)
    except DockerNotFound:
        pass

    client.containers.run(
        image_for_mc(s.version),
        command=cmd,
        name=name,
        detach=True,
        tty=True,
        stdin_open=True,
        volumes={d: {"bind": "/server", "mode": "rw"}},
        ports={"25565/tcp": s.port, "25575/tcp": 25575 + s.id},
        mem_limit=f"{s.ram_max}m",
        memswap_limit=f"{s.ram_max + s.swap_mb}m",
        cpu_period=100000,
        cpu_quota=int(s.cpu_cores * 100000),
        working_dir="/server",
        environment={"EULA": "TRUE"}
    )
    
    s.status = "running"
    db.commit()

    if s.playit_enabled and user.playit_agent_secret:
        try:
            start_playit_container(s.id, user.playit_agent_secret)
            tunnel_id, domain, detail = ensure_playit_tunnel(s, user)
            if tunnel_id:
                s.playit_tunnel_id = tunnel_id
                s.playit_domain = domain
                db.commit()
            elif detail:
                logger.warning("Failed to auto-create Playit tunnel for server %s on start: %s", s.id, detail)
        except Exception as exc:
            logger.warning("Failed to start local Playit agent for server %s: %s", s.id, exc)

    return {"status": "started"}

class AcceptEulaRequest(BaseModel):
    accept: bool = True


@router.post("/{sid}/accept-eula")
def accept_eula(sid: int, data: AcceptEulaRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s:
        raise HTTPException(404, "Not found")
    if not data.accept:
        raise HTTPException(400, "EULA acceptance is required")
    write_eula_accept(sid, s.name)
    return {"accepted": True}


@router.post("/{sid}/stop")
def stop_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        c = dc().containers.get(cname(sid))
        c.stop(timeout=30)
    except DockerNotFound:
        pass
    except Exception as e:
        print(f"Stop error: {e}")
    
    s.status = "stopped"
    db.commit()
    stop_playit_container(s.id)
    return {"status": "stopped"}

@router.post("/{sid}/restart")
async def restart_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stop_server(sid, db, user)
    return await start_server(sid=sid, data=None, db=db, user=user)

@router.delete("/{sid}")
async def delete_server(sid: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not s: raise HTTPException(404, "Not found")
    
    try:
        c = dc().containers.get(cname(sid))
        c.kill()
        c.remove(force=True)
    except: pass
    d = sdir(sid, s.name)
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
        except PermissionError:
            import subprocess as _sp
            _sp.run(["sudo", "rm", "-rf", d], check=False)

    stop_playit_container(s.id)
    db.delete(s)
    db.commit()

    remaining_playit_servers = db.query(Server).filter(
        Server.owner_id == user.id,
        Server.playit_enabled == True,  # noqa: E712
    ).count()
    if remaining_playit_servers == 0:
        user.playit_agent_id = None
        user.playit_agent_secret = None
        db.commit()

    return {"status": "deleted"}

class ResourcesUpdate(BaseModel):
    ram_min: Optional[int] = Field(default=None, ge=256, le=MAX_RAM_MB)
    ram_max: Optional[int] = Field(default=None, ge=256, le=MAX_RAM_MB)
    cpu_cores: Optional[int] = Field(default=None, ge=1, le=MAX_CPU_CORES)
    swap_mb: Optional[int] = Field(default=None, ge=0, le=MAX_SWAP_MB)
    custom_launch_command: Optional[str] = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def validate_memory(self):
        if self.ram_min is not None and self.ram_max is not None and self.ram_min > self.ram_max:
            raise ValueError("Minimum RAM cannot be greater than maximum RAM")
        return self


@router.put("/{sid}/resources")
def update_resources(sid: int, data: ResourcesUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == sid, Server.owner_id == user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    if get_status(sid) == "running":
        raise HTTPException(status_code=400, detail="Stop the server before changing resource settings.")

    new_ram_min = data.ram_min if data.ram_min is not None else server.ram_min
    new_ram_max = data.ram_max if data.ram_max is not None else server.ram_max
    if new_ram_min > new_ram_max:
        raise HTTPException(status_code=400, detail="Minimum RAM cannot be greater than maximum RAM.")

    if data.ram_min is not None:
        server.ram_min = data.ram_min
    if data.ram_max is not None:
        server.ram_max = data.ram_max
    if data.cpu_cores is not None:
        server.cpu_cores = data.cpu_cores
    if data.swap_mb is not None:
        server.swap_mb = data.swap_mb
    if data.custom_launch_command is not None:
        server.custom_launch_command = data.custom_launch_command.strip() or None
    db.commit()
    db.refresh(server)
    return to_dict(server)


@router.post("/cleanup")
def cleanup_containers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin only")
    valid_ids = {s.id for s in db.query(Server.id).all()}
    removed = []
    try:
        for c in dc().containers.list(all=True):
            if c.name.startswith("mc-panel-"):
                try:
                    cid = int(c.name.replace("mc-panel-", ""))
                    if cid not in valid_ids:
                        c.kill()
                        c.remove(force=True)
                        removed.append(c.name)
                except:
                    pass
    except:
        pass
    return {"removed": removed}
