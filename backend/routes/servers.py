import os
import re
import logging
import httpx
import asyncio
import contextlib
import shutil
import docker
import shlex
import platform
import subprocess
import stat
import time
from datetime import datetime
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
from .sftp import cleanup_sftp_server_artifacts
from utils.docker_client import get_docker_client
from utils.docker_cleanup import IS_DOCKER_DESKTOP_HOST, remove_container_if_exists

router = APIRouter(prefix="/api/servers", tags=["servers"])
logger = logging.getLogger(__name__)

IMAGE = "mc-panel-server"
PREFIX = "mc-panel"
HELPER_PREFIX = "mc-panel-helper"
MANAGED_CONTAINER_PREFIXES = (
    "mc-panel-",
    "mc-playit-",
    "mc-panel-sftp-",
)
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


def helper_container_name(purpose: str) -> str:
    return f"{HELPER_PREFIX}-{purpose}-{os.getpid()}-{time.time_ns()}"


def managed_container_server_id(container_name: str) -> int | None:
    for prefix in MANAGED_CONTAINER_PREFIXES:
        if container_name.startswith(prefix):
            suffix = container_name[len(prefix):]
            try:
                return int(suffix)
            except ValueError:
                return None
    return None


def eula_file(sid: int, name: str) -> str:
    return os.path.join(sdir(sid, name), "eula.txt")


def has_accepted_eula(sid: int, name: str) -> bool:
    path = eula_file(sid, name)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            return "eula=true" in f.read().lower()
    except OSError as exc:
        logger.warning("Could not read EULA file %s: %s", path, exc)
        return False

def java_version_for_mc(mc_version: str) -> int:
    try:
        parts = mc_version.split(".")
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return 21
    if minor >= 26:
        return 25
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
    if v == 25:
        return f"{IMAGE}:java25"
    return f"{IMAGE}:latest"


def java_cmd(version: str) -> str:
    return "/opt/java/openjdk/bin/java"


def ensure_runtime_images(client) -> None:
    base = os.path.dirname(os.path.dirname(__file__))
    build_errors: list[str] = []

    for tag, dockerfile in [
        ("latest", "Dockerfile"),
        ("java25", "Dockerfile.java25"),
        ("java17", "Dockerfile.java17"),
        ("java11", "Dockerfile.java11"),
    ]:
        image_name = f"{IMAGE}:{tag}"
        try:
            client.images.get(image_name)
            continue
        except Exception:
            pass

        try:
            client.images.build(path=base, tag=image_name, dockerfile=dockerfile)
        except Exception as exc:
            build_errors.append(f"{image_name}: {exc}")

    if build_errors:
        raise HTTPException(
            status_code=500,
            detail="Docker images could not be built. Make sure Docker Desktop is running and try again. "
            + " | ".join(build_errors),
        )


def server_properties_file(sid: int, name: str) -> str:
    return os.path.join(sdir(sid, name), "server.properties")


def container_relative_path(path: str, root: str) -> str:
    return os.path.relpath(path, root).replace("\\", "/")


def find_unix_args(root: str) -> str | None:
    ua_root = os.path.join(root, "unix_args.txt")
    if os.path.exists(ua_root):
        return ua_root

    for root_dir, _dirs, files in os.walk(root):
        if "unix_args.txt" in files and root_dir != root:
            return os.path.join(root_dir, "unix_args.txt")
    return None


def version_sort_key(value: str) -> tuple[int, ...]:
    parts = [int(part) for part in re.findall(r"\d+", value)]
    return tuple(parts) if parts else (0,)


def extract_forge_mc_version(value: str) -> str | None:
    if not value:
        return None
    mc_ver = value.split("-", 1)[0].strip()
    if not re.fullmatch(r"\d+(?:\.\d+){1,3}", mc_ver):
        return None
    return mc_ver


def extract_neoforge_mc_version(value: str) -> str | None:
    if not value:
        return None
    parts = value.split(".")
    if len(parts) < 2 or not all(part.isdigit() for part in parts[:2]):
        return None
    first = int(parts[0])
    second = int(parts[1])
    if first == 1:
        if len(parts) < 3 or not parts[2].isdigit():
            return None
        return f"1.{second}.{parts[2]}"
    return f"{first}.{second}"


def unique_versions_desc(values: list[str]) -> list[str]:
    deduped = {value for value in values if value}
    return sorted(deduped, key=version_sort_key, reverse=True)


def remove_server_dir(path: str) -> None:
    if not os.path.exists(path):
        return

    def _clear_readonly(func, target, _exc_info):
        try:
            os.chmod(target, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        except OSError:
            pass
        func(target)

    def _remove_with_docker() -> bool:
        parent = os.path.dirname(os.path.abspath(path))
        name = os.path.basename(path)
        try:
            dc().containers.run(
                f"{IMAGE}:latest",
                name=helper_container_name("server-rm"),
                command=["sh", "-lc", 'rm -rf "/target/$TARGET_NAME"'],
                environment={"TARGET_NAME": name},
                remove=True,
                labels={"enderpanel.helper": "true", "enderpanel.purpose": "server-rm"},
                volumes={parent: {"bind": "/target", "mode": "rw"}},
            )
            return not os.path.exists(path)
        except Exception as exc:
            logger.warning("Docker-assisted server dir cleanup failed for %s: %s", path, exc)
            return False

    def _remove_with_platform_command() -> bool:
        system = platform.system()
        try:
            if system == "Windows":
                subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", path], check=False)
            elif system == "Darwin":
                subprocess.run(["rm", "-rf", path], check=False)
            else:
                subprocess.run(["rm", "-rf", path], check=False)
        except Exception as exc:
            logger.warning("Platform cleanup command failed for %s: %s", path, exc)
        return not os.path.exists(path)

    try:
        shutil.rmtree(path, onerror=_clear_readonly if os.name == "nt" else None)
        return
    except (PermissionError, OSError) as exc:
        logger.warning("Standard server dir cleanup failed for %s: %s", path, exc)

    if IS_DOCKER_DESKTOP_HOST:
        if _remove_with_docker() or _remove_with_platform_command():
            return
    else:
        if _remove_with_platform_command() or _remove_with_docker():
            return

    if platform.system() != "Windows":
        subprocess.run(["sudo", "rm", "-rf", path], check=False)
        if not os.path.exists(path):
            return

    raise PermissionError(f"Could not remove server directory {path}")


def cleanup_server_runtime_artifacts(server_id: int) -> None:
    try:
        remove_container_if_exists(cname(server_id), stop_timeout=10)
    except Exception as exc:
        logger.warning("Failed to remove server container %s: %s", cname(server_id), exc)

    stop_playit_container(server_id)
    cleanup_sftp_server_artifacts(server_id)


def cleanup_orphaned_sftp_state(valid_ids: set[int]) -> list[str]:
    removed_states: list[str] = []
    try:
        for entry in os.listdir(os.path.dirname(SERVERS_DIR)):
            match = re.fullmatch(r"sftp_state_(\d+)\.json", entry)
            if not match:
                continue
            server_id = int(match.group(1))
            if server_id in valid_ids:
                continue
            cleanup_sftp_server_artifacts(server_id)
            removed_states.append(entry)
    except Exception as exc:
        logger.warning("Failed to clean orphaned SFTP state files: %s", exc)
    return removed_states


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

                    installer = os.path.join(path, "neoforge-installer.jar")
                    with open(installer, "wb") as f:
                        f.write(r.content)

                    if os.path.exists(installer) and os.path.getsize(installer) > 50000:
                        return True, None
                    return False, "NeoForge installer downloaded, but the file looks incomplete."
                except Exception as e:
                    print(f"NeoForge download error: {e}")
                    return False, f"NeoForge download error: {e}"
            elif stype == "forge":
                try:
                    r = await c.get(f"https://maven.minecraftforge.net/net/minecraftforge/forge/maven-metadata.xml")
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(r.text)
                    versions = root.findall(".//version")
                    matching = [
                        v.text for v in versions
                        if v.text and extract_forge_mc_version(v.text) == ver
                    ]
                    if not matching:
                        return False, f"No Forge builds found for {ver}."

                    forge_ver = sorted(matching, key=version_sort_key)[-1]
                    installer_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_ver}/forge-{forge_ver}-installer.jar"
                    r = await c.get(installer_url)
                    
                    if r.status_code != 200:
                        return False, f"Forge installer download failed with status {r.status_code}."

                    installer = os.path.join(path, "forge-installer.jar")
                    with open(installer, "wb") as f:
                        f.write(r.content)

                    if os.path.exists(installer) and os.path.getsize(installer) > 50000:
                        return True, None
                    return False, "Forge installer downloaded, but the file looks incomplete."
                except Exception as e:
                    print(f"Forge download error: {e}")
                    return False, f"Forge download error: {e}"
    except Exception as e:
        print(f"Download error: {e}")
        return False, f"Download error: {e}"

    return False, f"Unsupported server type or installer failed for {stype} {ver}."


async def ensure_modded_server_layout(server: Server, path: str) -> tuple[bool, str | None]:
    if server.server_type not in {"forge", "neoforge"}:
        return True, None

    if find_unix_args(path):
        return True, None

    installer_name = "neoforge-installer.jar" if server.server_type == "neoforge" else "forge-installer.jar"
    installer_path = os.path.join(path, installer_name)
    if not os.path.exists(installer_path):
        return False, f"Missing {installer_name}. Recreate the server to download the installer again."

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "run", "--rm",
            "-v", f"{path}:/server",
            "-w", "/server",
            image_for_mc(server.version),
            "/opt/java/openjdk/bin/java",
            "-jar", installer_name,
            "--installServer",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
    except asyncio.TimeoutError:
        if proc is not None:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            await proc.communicate()
        return False, f"{server.server_type.capitalize()} installer timed out. Please try starting the server again."
    except Exception as exc:
        return False, f"{server.server_type.capitalize()} installer failed to start: {exc}"

    if proc.returncode != 0:
        detail = (stderr or stdout).decode("utf-8", errors="replace").strip()
        return False, detail or f"{server.server_type.capitalize()} installer exited with code {proc.returncode}."

    if find_unix_args(path):
        return True, None

    if server.server_type == "forge" and os.path.exists(os.path.join(path, "libraries")):
        return True, None

    return False, f"{server.server_type.capitalize()} installer finished, but no launch files were created."

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
                versions = unique_versions_desc([
                    mc_ver
                    for mc_ver in (extract_forge_mc_version(v) for v in all_versions)
                    if mc_ver
                ])
            elif server_type == "neoforge":
                r = await c.get("https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml")
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                all_versions = [v.text for v in root.findall(".//version") if v.text]
                versions = unique_versions_desc([
                    mc_ver
                    for mc_ver in (extract_neoforge_mc_version(v) for v in all_versions)
                    if mc_ver
                ])
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
        custom_launch_command=data.custom_launch_command, created_at=datetime.utcnow())
    db.add(s); db.commit(); db.refresh(s)
    d = sdir(s.id, s.name)
    remove_server_dir(d)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "eula.txt"), "w", encoding="utf-8") as f:
        f.write("eula=false\n")
    ensure_server_properties(s.id, s.name, port, data.max_players, data.motd)
    ok, download_error = await download_jar(data.server_type, data.version, d)
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
        remove_container_if_exists(name, stop_timeout=5)
    except DockerNotFound:
        pass
    except HTTPException:
        raise
    
    d = sdir(sid, s.name)
    ensure_server_properties(sid, s.name, s.port, s.max_players, s.motd)

    if not has_accepted_eula(sid, s.name):
        if data and data.accept_eula:
            write_eula_accept(sid, s.name)
        else:
            raise HTTPException(400, "EULA acceptance required")

    ok, install_error = await ensure_modded_server_layout(s, d)
    if not ok:
        raise HTTPException(status_code=400, detail=install_error or "Failed to prepare server files")

    ensure_runtime_images(client)
    
    java = java_cmd(s.version)
    if s.custom_launch_command:
        cmd = s.custom_launch_command.replace("{jar}", "server.jar").replace("{ram_min}", str(s.ram_min))
        cmd = shlex.split(cmd.replace("{ram_max}", str(s.ram_max)).replace("{java}", java))
    else:
        unix_args = find_unix_args(d)

        server_jar = os.path.join(d, "server.jar")
        has_server_jar = (
            os.path.exists(server_jar)
            and os.path.isfile(server_jar)
            and os.access(server_jar, os.R_OK)
            and os.path.getsize(server_jar) > 50000
        )

        if unix_args:
            with open(os.path.join(d, "user_jvm_args.txt"), "w") as f:
                f.write(f"-Xmx{s.ram_max}M\n-Xms{s.ram_min}M\n-XX:+UseG1GC\n")
            ua_rel = container_relative_path(unix_args, d)
            # Forge/NeoForge installers generate unix_args.txt with the correct launch entrypoint.
            cmd = [java, "@user_jvm_args.txt", f"@{ua_rel}", "nogui"]
        elif has_server_jar:
            cmd = [java, f"-Xmx{s.ram_max}M", f"-Xms{s.ram_min}M", "-jar", "server.jar", "nogui"]
        else:
            raise HTTPException(400, "No server files found")

    # Always clean up any leftover container before creating
    try:
        remove_container_if_exists(name, stop_timeout=5)
    except DockerNotFound:
        pass

    try:
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
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Docker container. Make sure Docker Desktop is running. {exc}",
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

    cleanup_server_runtime_artifacts(sid)
    d = sdir(sid, s.name)
    remove_server_dir(d)

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
            cid = managed_container_server_id(c.name)
            if cid is None or cid in valid_ids:
                continue

            try:
                if c.name.startswith("mc-panel-sftp-"):
                    cleanup_sftp_server_artifacts(cid)
                else:
                    remove_container_if_exists(c.name, stop_timeout=5)
                removed.append(c.name)
            except Exception as exc:
                logger.warning("Failed to remove orphaned managed container %s: %s", c.name, exc)
    except Exception as exc:
        logger.warning("Managed container cleanup failed: %s", exc)
    removed.extend(cleanup_orphaned_sftp_state(valid_ids))
    return {"removed": removed}
