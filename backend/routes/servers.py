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
import json
import uuid
from datetime import datetime
from docker.errors import NotFound as DockerNotFound
from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Any
from database import get_db
from models.user import User
from models.server import Server
from models.panel_setting import PanelSetting
from utils.security import get_current_user
from config import SERVERS_DIR, PEARLS_DIR
from .domain_runtime import delete_public_domain_record
from .playit_runtime import stop_playit_container, start_playit_container, ensure_playit_tunnel, read_playit_secret_from_disk
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
PEARL_MANIFEST = ".enderpanel-pearl.json"
PEARL_INSTALL_SCRIPT = ".enderpanel-pearl-install.sh"
PEARLS_ENABLED_KEY = "pearls_enabled"
PEARLS_ADMIN_ONLY_UPLOAD_KEY = "pearls_admin_only_upload"
PEARL_ALLOWED_RUNTIME_PLACEHOLDERS = {
    "SERVER_MEMORY": "{ram_max}",
    "SERVER_MEMORY_MB": "{ram_max}",
    "SERVER_PORT": "{port}",
    "SERVER_MAX_PLAYERS": "{max_players}",
}

def sanitize(n: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', n)

def sdir(sid: int, name: str) -> str:
    return os.path.join(SERVERS_DIR, f"{sid}-{sanitize(name)}")

def cname(sid: int) -> str:
    return f"{PREFIX}-{sid}"

def dc():
    return get_docker_client()


def runtime_uid_gid() -> tuple[int, int]:
    try:
        uid = os.getuid()
    except AttributeError:
        uid = 1000

    try:
        gid = os.getgid()
    except AttributeError:
        gid = 1000

    # Never run the Minecraft process as root inside the container.
    if uid <= 0:
        uid = 1000
    if gid <= 0:
        gid = 1000

    return uid, gid


def runtime_user_spec() -> str:
    uid, gid = runtime_uid_gid()
    return f"{uid}:{gid}"


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


def pearl_manifest_file(sid: int, name: str) -> str:
    return os.path.join(sdir(sid, name), PEARL_MANIFEST)


def pearl_install_script_file(path: str) -> str:
    return os.path.join(path, PEARL_INSTALL_SCRIPT)


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
        major = int(parts[0]) if parts else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return 21
    if major >= 26:
        return 25
    if major != 1:
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


def terminal_jvm_args() -> list[str]:
    return [
        "-Dterminal.jline=false",
        "-Dterminal.ansi=true",
    ]


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
    second = parts[1]
    if first < 26:
        return f"1.{first}.{second}"
    return f"{first}.{second}"


def unique_versions_desc(values: list[str]) -> list[str]:
    deduped = {value for value in values if value}
    return sorted(deduped, key=version_sort_key, reverse=True)


def is_stable_minecraft_version(value: str) -> bool:
    return bool(re.fullmatch(r"\d+(?:\.\d+){1,2}", value))


def normalize_pearl_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return default
    text = str(value).strip()
    return text or default


def extract_pearl_root(payload: dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload.get("attributes"), dict):
        return payload["attributes"]
    return payload


def normalize_pearl_docker_images(raw: Any) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            key_text = normalize_pearl_text(key)
            value_text = normalize_pearl_text(value)
            if not key_text and not value_text:
                continue
            if "/" in key_text or ":" in key_text:
                image = key_text
                label = value_text or key_text
            else:
                image = value_text or key_text
                label = key_text or image
            if image:
                images.append({"label": label, "image": image})
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                image = normalize_pearl_text(item.get("image") or item.get("value") or item.get("docker_image"))
                label = normalize_pearl_text(item.get("label") or item.get("name"), image)
            else:
                image = normalize_pearl_text(item)
                label = image
            if image:
                images.append({"label": label, "image": image})
    elif isinstance(raw, str):
        value = raw.strip()
        if value:
            images.append({"label": value, "image": value})

    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in images:
        if item["image"] in seen:
            continue
        seen.add(item["image"])
        deduped.append(item)
    return deduped


def normalize_pearl_variables(raw: Any) -> list[dict[str, Any]]:
    items: list[Any] = []
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and isinstance(raw.get("data"), list):
        items = raw["data"]

    variables: list[dict[str, Any]] = []
    for item in items:
        source = item.get("attributes") if isinstance(item, dict) and isinstance(item.get("attributes"), dict) else item
        if not isinstance(source, dict):
            continue
        key = normalize_pearl_text(source.get("env_variable") or source.get("key") or source.get("name"))
        if not key:
            continue
        rules = normalize_pearl_text(source.get("rules"))
        variables.append(
            {
                "key": key,
                "name": normalize_pearl_text(source.get("name"), key.replace("_", " ").title()),
                "description": normalize_pearl_text(source.get("description")),
                "default_value": normalize_pearl_text(
                    source.get("default_value") if source.get("default_value") is not None else source.get("default")
                ),
                "rules": rules,
                "required": "required" in rules,
                "user_viewable": bool(source.get("user_viewable", True)),
                "user_editable": bool(source.get("user_editable", True)),
            }
        )
    return variables


def infer_pearl_server_type(name: str, startup: str, variables: list[dict[str, Any]], docker_images: list[dict[str, str]]) -> str:
    haystack = " ".join(
        [
            name.lower(),
            startup.lower(),
            " ".join(variable["key"].lower() for variable in variables),
            " ".join(item["image"].lower() for item in docker_images),
        ]
    )
    if "neoforge" in haystack:
        return "neoforge"
    if "forge" in haystack:
        return "forge"
    if "fabric" in haystack:
        return "fabric"
    if "paper" in haystack or "purpur" in haystack or "spigot" in haystack:
        return "paper"
    return "vanilla"


def infer_pearl_version(variables: list[dict[str, Any]]) -> str:
    for key in ("MC_VERSION", "MINECRAFT_VERSION", "SERVER_VERSION"):
        for variable in variables:
            if variable["key"] == key and re.fullmatch(r"\d+(?:\.\d+){1,3}", variable["default_value"]):
                return variable["default_value"]
    return "1.21.11"


def normalize_pearl_payload(payload: dict[str, Any]) -> dict[str, Any]:
    root = extract_pearl_root(payload)
    scripts = root.get("scripts") if isinstance(root.get("scripts"), dict) else {}
    installation = scripts.get("installation") if isinstance(scripts.get("installation"), dict) else {}
    variables = normalize_pearl_variables(
        root.get("variables")
        or (root.get("relationships") or {}).get("variables")
        or []
    )
    docker_images = normalize_pearl_docker_images(root.get("docker_images"))
    startup = normalize_pearl_text(root.get("startup"))
    name = normalize_pearl_text(root.get("name"), "Imported Egg")
    description = normalize_pearl_text(root.get("description"))
    install_script = normalize_pearl_text(installation.get("script"))
    install_container = normalize_pearl_text(installation.get("container"))
    return {
        "name": name,
        "description": description,
        "startup": startup,
        "docker_images": docker_images,
        "variables": variables,
        "install_script": install_script,
        "install_container": install_container,
        "inferred_server_type": infer_pearl_server_type(name, startup, variables, docker_images),
        "suggested_version": infer_pearl_version(variables),
    }


PEARL_PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")


def fill_pearl_placeholders(template: str, values: dict[str, str]) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return values.get(key, match.group(0))

    return PEARL_PLACEHOLDER_PATTERN.sub(replace, template)


def unresolved_pearl_placeholders(template: str) -> list[str]:
    return sorted({match.group(1) for match in PEARL_PLACEHOLDER_PATTERN.finditer(template)})


def read_pearl_manifest(sid: int, name: str) -> dict[str, Any] | None:
    path = pearl_manifest_file(sid, name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except Exception as exc:
        logger.warning("Could not read pearl manifest for server %s: %s", sid, exc)
        return None


def write_pearl_manifest(path: str, payload: dict[str, Any]) -> None:
    with open(os.path.join(path, PEARL_MANIFEST), "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def remove_pearl_install_script(path: str) -> None:
    with contextlib.suppress(OSError):
        os.remove(pearl_install_script_file(path))


def is_pterodactyl_yolk_image(image: str) -> bool:
    normalized = normalize_pearl_text(image).lower()
    return "ghcr.io/ptero-eggs/yolks:" in normalized or "quay.io/pterodactyl/core:" in normalized


def pearl_library_file(pearl_id: str) -> str:
    return os.path.join(PEARLS_DIR, f"{pearl_id}.json")


def get_bool_panel_setting(db: Session, key: str, default: bool) -> bool:
    setting = db.query(PanelSetting).filter(PanelSetting.key == key).first()
    if not setting:
        setting = PanelSetting(key=key, value="1" if default else "0")
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return str(setting.value).strip().lower() in {"1", "true", "yes", "on"}


def get_pearl_feature_flags(db: Session) -> dict[str, bool]:
    enabled = get_bool_panel_setting(db, PEARLS_ENABLED_KEY, True)
    admin_only_upload = get_bool_panel_setting(db, PEARLS_ADMIN_ONLY_UPLOAD_KEY, False)
    return {
        "enabled": enabled,
        "admin_only_upload": admin_only_upload,
    }


def ensure_pearls_enabled(db: Session) -> dict[str, bool]:
    flags = get_pearl_feature_flags(db)
    if not flags["enabled"]:
        raise HTTPException(status_code=403, detail="Pterodactyl egg imports are disabled by the panel admin.")
    return flags


def ensure_pearl_upload_allowed(user: User, db: Session) -> dict[str, bool]:
    flags = ensure_pearls_enabled(db)
    if flags["admin_only_upload"] and not user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can upload Pterodactyl egg JSON files.")
    return flags


def pearl_slug(name: str) -> str:
    base = sanitize(name).strip("_").lower() or "egg"
    return f"{base}-{uuid.uuid4().hex[:8]}"


def list_library_pearls() -> list[dict[str, Any]]:
    pearls: list[dict[str, Any]] = []
    try:
        for entry in os.listdir(PEARLS_DIR):
            if not entry.endswith(".json"):
                continue
            path = os.path.join(PEARLS_DIR, entry)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                if not isinstance(data, dict):
                    continue
                pearls.append(
                    {
                        "id": normalize_pearl_text(data.get("id"), entry[:-5]),
                        "name": normalize_pearl_text(data.get("name"), "Imported Egg"),
                        "description": normalize_pearl_text(data.get("description")),
                        "server_type": normalize_pearl_text(data.get("inferred_server_type"), "paper"),
                        "suggested_version": normalize_pearl_text(data.get("suggested_version"), "1.21.11"),
                        "docker_image": normalize_pearl_text((data.get("docker_images") or [{}])[0].get("image") if data.get("docker_images") else ""),
                        "uploaded_at": normalize_pearl_text(data.get("uploaded_at")),
                    }
                )
            except Exception as exc:
                logger.warning("Skipping unreadable pearl library item %s: %s", path, exc)
    except FileNotFoundError:
        os.makedirs(PEARLS_DIR, exist_ok=True)
    return sorted(pearls, key=lambda item: (item.get("uploaded_at") or "", item.get("name") or ""), reverse=True)


def read_library_pearl(pearl_id: str) -> dict[str, Any]:
    path = pearl_library_file(pearl_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Egg not found.")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read saved egg: {exc}")
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Saved egg is invalid.")
    return data


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
    pearl_manifest = read_pearl_manifest(s.id, s.name)
    return {
        "id": s.id, "name": s.name, "status": s.status, "server_type": s.server_type,
        "port": s.port, "max_players": s.max_players, "version": s.version, "motd": s.motd,
        "ram_min": s.ram_min, "ram_max": s.ram_max, "swap_mb": s.swap_mb, "cpu_cores": s.cpu_cores,
        "custom_launch_command": s.custom_launch_command,
        "is_pearl": bool(pearl_manifest),
        "pearl_name": pearl_manifest.get("name") if pearl_manifest else None,
        "avatar": f"/api/avatars/{s.avatar}" if s.avatar else None,  # type: ignore[union-attr]
        "eula_accepted": has_accepted_eula(s.id, s.name),
        "container_started_at": get_container_started_at(s.id),
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "public_domain_enabled": s.public_domain_enabled,
        "public_domain_subdomain": s.public_domain_subdomain,
        "public_domain": s.public_domain,
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
    except Exception:
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


class CreatePearl(BaseModel):
    library_id: Optional[str] = Field(default=None, max_length=160)
    name: str = Field(min_length=1, max_length=100)
    pearl_name: str = Field(min_length=1, max_length=120)
    server_type: str = "paper"
    port: int = Field(default=25565, ge=MIN_SERVER_PORT, le=MAX_SERVER_PORT)
    max_players: int = Field(default=20, ge=1, le=1000)
    version: str = Field(default="1.21.11", min_length=1, max_length=32, pattern=r"^[A-Za-z0-9._+\-]+$")
    motd: str = Field(default="A Minecraft Server", max_length=255)
    ram_min: int = Field(default=512, ge=256, le=MAX_RAM_MB)
    ram_max: int = Field(default=1024, ge=256, le=MAX_RAM_MB)
    swap_mb: int = Field(default=512, ge=0, le=MAX_SWAP_MB)
    cpu_cores: int = Field(default=1, ge=1, le=MAX_CPU_CORES)
    runtime_image: Optional[str] = Field(default=None, max_length=255)
    startup: str = Field(min_length=1, max_length=4096)
    install_script: Optional[str] = Field(default=None, max_length=60000)
    install_container: Optional[str] = Field(default=None, max_length=255)
    variables: dict[str, str] = Field(default_factory=dict)

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

    @field_validator("runtime_image", "install_container")
    @classmethod
    def normalize_optional_image(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("startup")
    @classmethod
    def normalize_startup(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Egg startup command is required")
        return cleaned

    @field_validator("variables")
    @classmethod
    def normalize_variables(cls, value: dict[str, str]) -> dict[str, str]:
        cleaned: dict[str, str] = {}
        for key, raw in value.items():
            env_key = normalize_pearl_text(key).upper()
            if not re.fullmatch(r"[A-Z0-9_]+", env_key):
                raise ValueError(f"Invalid pearl variable name: {key}")
            cleaned[env_key] = normalize_pearl_text(raw)
        return cleaned

    @model_validator(mode="after")
    def validate_memory(self):
        if self.ram_min > self.ram_max:
            raise ValueError("Minimum RAM cannot be greater than maximum RAM")
        return self


async def run_pearl_install_script(
    server_id: int,
    path: str,
    container_image: str,
    install_script: str,
    env: dict[str, str],
) -> tuple[bool, str | None]:
    helper_name = f"{HELPER_PREFIX}-pearl-install-{server_id}"
    script_path = pearl_install_script_file(path)
    try:
        normalized_script = install_script.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
        if normalized_script.startswith("#!"):
            script_body = normalized_script
        else:
            script_body = "#!/bin/sh\nset -e\n" + normalized_script
        with open(script_path, "w", encoding="utf-8") as handle:
            handle.write(script_body)
            if not script_body.endswith("\n"):
                handle.write("\n")
        os.chmod(script_path, 0o755)

        args = [
            "docker", "run", "--rm",
            "--name", helper_name,
            "--label", "enderpanel.helper=true",
            "--label", f"enderpanel.server_id={server_id}",
            "--label", "enderpanel.purpose=pearl-install",
            "--user", runtime_user_spec(),
            "-v", f"{path}:/mnt/server",
            "-w", "/mnt/server",
        ]
        for key, value in env.items():
            args.extend(["-e", f"{key}={value}"])
        args.extend([container_image, f"/mnt/server/{PEARL_INSTALL_SCRIPT}"])

        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
    except asyncio.TimeoutError:
        with contextlib.suppress(Exception):
            remove_container_if_exists(helper_name, stop_timeout=1)
        return False, "Egg install script timed out."
    except Exception as exc:
        with contextlib.suppress(Exception):
            remove_container_if_exists(helper_name, stop_timeout=1)
        return False, f"Egg install script failed to start: {exc}"
    finally:
        remove_pearl_install_script(path)
        with contextlib.suppress(Exception):
            remove_container_if_exists(helper_name, stop_timeout=1)

    if proc.returncode != 0:
        detail = (stderr or stdout).decode("utf-8", errors="replace").strip()
        return False, detail or f"Egg install script exited with code {proc.returncode}."

    return True, None

async def download_jar(stype: str, ver: str, path: str) -> tuple[bool, str | None]:
    jar = os.path.join(path, "server.jar")
    try:
        async with httpx.AsyncClient(timeout=300) as c:
            if stype == "paper":
                r = await c.get(f"https://fill.papermc.io/v3/projects/paper/versions/{ver}/builds")
                builds = r.json()
                if not isinstance(builds, list) or not builds:
                    return False, f"No Paper builds found for {ver}."
                build = next((item for item in builds if item.get("channel") == "STABLE"), builds[0])
                download = ((build.get("downloads") or {}).get("server:default") or {})
                download_url = download.get("url")
                if not download_url:
                    return False, f"Paper build metadata for {ver} did not include a server download."
                r = await c.get(download_url)
                with open(jar, "wb") as f:
                    f.write(r.content)
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
    installer_container_name = f"{HELPER_PREFIX}-installer-{server.id}"
    try:
        with contextlib.suppress(Exception):
            remove_container_if_exists(installer_container_name, stop_timeout=5)
        runtime_user = runtime_user_spec()
        proc = await asyncio.create_subprocess_exec(
            "docker", "run", "--rm",
            "--name", installer_container_name,
            "--label", "enderpanel.helper=true",
            "--label", f"enderpanel.server_id={server.id}",
            "--label", f"enderpanel.purpose={server.server_type}-installer",
            "--user", runtime_user,
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
        with contextlib.suppress(Exception):
            remove_container_if_exists(installer_container_name, stop_timeout=1)
        return False, f"{server.server_type.capitalize()} installer timed out. Please try starting the server again."
    except Exception as exc:
        with contextlib.suppress(Exception):
            remove_container_if_exists(installer_container_name, stop_timeout=1)
        return False, f"{server.server_type.capitalize()} installer failed to start: {exc}"
    finally:
        with contextlib.suppress(Exception):
            remove_container_if_exists(installer_container_name, stop_timeout=1)

    if proc.returncode != 0:
        detail = (stderr or stdout).decode("utf-8", errors="replace").strip()
        return False, detail or f"{server.server_type.capitalize()} installer exited with code {proc.returncode}."

    if find_unix_args(path):
        return True, None

    if server.server_type == "forge" and os.path.exists(os.path.join(path, "libraries")):
        return True, None

    return False, f"{server.server_type.capitalize()} installer finished, but no launch files were created."


def build_pearl_runtime_values(server: CreatePearl, port: int) -> dict[str, str]:
    values = {key: normalize_pearl_text(value) for key, value in server.variables.items()}
    values.setdefault("SERVER_MEMORY", "{ram_max}")
    values.setdefault("SERVER_MEMORY_MB", "{ram_max}")
    values.setdefault("SERVER_PORT", "{port}")
    values.setdefault("SERVER_MAX_PLAYERS", str(server.max_players))
    values.setdefault("SERVER_JARFILE", "server.jar")
    return values


def build_pearl_install_values(server: CreatePearl, port: int) -> dict[str, str]:
    values = {key: normalize_pearl_text(value) for key, value in server.variables.items()}
    values.setdefault("SERVER_MEMORY", str(server.ram_max))
    values.setdefault("SERVER_MEMORY_MB", str(server.ram_max))
    values.setdefault("SERVER_PORT", str(port))
    values.setdefault("SERVER_MAX_PLAYERS", str(server.max_players))
    values.setdefault("SERVER_JARFILE", "server.jar")
    values.setdefault("STARTUP", fill_pearl_placeholders(server.startup, build_pearl_runtime_values(server, port)).replace("{ram_max}", str(server.ram_max)).replace("{port}", str(port)))
    return values


@router.post("/pearls/parse")
async def parse_pearl(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_pearl_upload_allowed(user, db)
    filename = file.filename or "pearl.json"
    if not filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Please upload a JSON egg file.")

    try:
        payload = json.loads((await file.read()).decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="That file is not valid JSON.")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Egg JSON must contain an object at the top level.")

    parsed = normalize_pearl_payload(payload)
    if not parsed["startup"]:
        raise HTTPException(status_code=400, detail="This egg does not include a startup command.")

    return parsed


@router.get("/pearls/config")
def get_pearl_config(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    flags = get_pearl_feature_flags(db)
    return {
        "enabled": flags["enabled"],
        "admin_only_upload": flags["admin_only_upload"],
        "can_upload": flags["enabled"] and (user.is_admin or not flags["admin_only_upload"]),
    }


@router.get("/pearls/library")
def get_pearl_library(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_pearls_enabled(db)
    return {"pearls": list_library_pearls()}


@router.get("/pearls/library/{pearl_id}")
def get_pearl_library_item(pearl_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ensure_pearls_enabled(db)
    return read_library_pearl(pearl_id)


@router.post("/pearls/library")
async def upload_pearl_library_item(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ensure_pearl_upload_allowed(user, db)
    filename = file.filename or "pearl.json"
    if not filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Please upload a JSON egg file.")

    try:
        payload = json.loads((await file.read()).decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="That file is not valid JSON.")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Egg JSON must contain an object at the top level.")

    parsed = normalize_pearl_payload(payload)
    if not parsed["startup"]:
        raise HTTPException(status_code=400, detail="This egg does not include a startup command.")

    pearl_id = pearl_slug(parsed["name"])
    stored = {
        **parsed,
        "id": pearl_id,
        "uploaded_at": datetime.utcnow().isoformat(),
        "uploaded_by": user.username,
        "source_filename": filename,
    }
    with open(pearl_library_file(pearl_id), "w", encoding="utf-8") as handle:
        json.dump(stored, handle, indent=2)
    return stored


@router.post("/pearls")
async def create_server_from_pearl(
    data: CreatePearl,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    flags = ensure_pearls_enabled(db)
    source_payload: dict[str, Any] | None = None
    if data.library_id:
        source_payload = read_library_pearl(data.library_id)
    if flags["admin_only_upload"] and not user.is_admin and source_payload is None:
        raise HTTPException(status_code=403, detail="Only admins can upload Pterodactyl egg JSON files. Pick one from the saved egg collection instead.")

    source_name = data.pearl_name
    source_startup = data.startup
    source_install_script = data.install_script
    source_install_container = data.install_container
    source_runtime_image = data.runtime_image
    source_server_type = data.server_type
    source_version = data.version
    source_variables = dict(data.variables)
    source_description = ""
    if source_payload is not None:
        source_name = normalize_pearl_text(source_payload.get("name"), source_name)
        source_description = normalize_pearl_text(source_payload.get("description"))
        source_startup = normalize_pearl_text(source_payload.get("startup"), source_startup)
        source_install_script = normalize_pearl_text(source_payload.get("install_script")) or source_install_script
        source_install_container = normalize_pearl_text(source_payload.get("install_container")) or source_install_container
        source_runtime_image = normalize_pearl_text(
            (source_payload.get("docker_images") or [{}])[0].get("image") if source_payload.get("docker_images") else None
        ) or source_runtime_image
        source_server_type = normalize_pearl_text(source_payload.get("inferred_server_type"), source_server_type)
        source_version = normalize_pearl_text(source_payload.get("suggested_version"), source_version)
        library_defaults = {
            variable["key"]: normalize_pearl_text(variable.get("default_value"))
            for variable in source_payload.get("variables", [])
            if isinstance(variable, dict) and variable.get("key")
        }
        library_defaults.update(source_variables)
        source_variables = library_defaults

    port = data.port
    while db.query(Server).filter(Server.port == port).first():
        port += 1
        if port > MAX_SERVER_PORT:
            raise HTTPException(status_code=400, detail="No available server ports")

    effective_data = data.model_copy(update={
        "pearl_name": source_name,
        "startup": source_startup,
        "install_script": source_install_script,
        "install_container": source_install_container,
        "runtime_image": source_runtime_image,
        "server_type": source_server_type,
        "version": source_version,
        "variables": source_variables,
    })

    runtime_values = build_pearl_runtime_values(effective_data, port)
    resolved_startup = fill_pearl_placeholders(effective_data.startup, runtime_values)
    unresolved_startup = unresolved_pearl_placeholders(resolved_startup)
    if unresolved_startup:
        raise HTTPException(
            status_code=400,
            detail=f"Egg startup is still missing values for: {', '.join(unresolved_startup)}",
        )

    install_values = build_pearl_install_values(effective_data, port)
    resolved_install_script = fill_pearl_placeholders(effective_data.install_script or "", install_values).strip()
    unresolved_install = unresolved_pearl_placeholders(resolved_install_script)
    if unresolved_install:
        raise HTTPException(
            status_code=400,
            detail=f"Egg install script is still missing values for: {', '.join(unresolved_install)}",
        )

    server = Server(
        name=effective_data.name,
        owner_id=user.id,
        server_type=effective_data.server_type,
        port=port,
        max_players=effective_data.max_players,
        version=effective_data.version,
        motd=effective_data.motd,
        ram_min=effective_data.ram_min,
        ram_max=effective_data.ram_max,
        swap_mb=effective_data.swap_mb,
        cpu_cores=effective_data.cpu_cores,
        custom_launch_command=resolved_startup,
        created_at=datetime.utcnow(),
    )
    db.add(server)
    db.commit()
    db.refresh(server)

    path = sdir(server.id, server.name)
    remove_server_dir(path)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "eula.txt"), "w", encoding="utf-8") as handle:
        handle.write("eula=false\n")
    ensure_server_properties(server.id, server.name, port, effective_data.max_players, effective_data.motd)

    runtime_image = effective_data.runtime_image or image_for_mc(effective_data.version)
    manifest = {
        "name": effective_data.pearl_name,
        "description": source_description,
        "library_id": effective_data.library_id,
        "runtime_image": runtime_image,
        "startup": resolved_startup,
        "install_container": effective_data.install_container,
        "variables": effective_data.variables,
        "imported_at": datetime.utcnow().isoformat(),
    }
    write_pearl_manifest(path, manifest)

    install_ran = False
    install_error = None
    if resolved_install_script:
        install_ran = True
        install_container = effective_data.install_container or runtime_image
        ok, install_error = await run_pearl_install_script(
            server.id,
            path,
            install_container,
            resolved_install_script,
            install_values,
        )
        if not ok:
            response = to_dict(server)
            response["install_ran"] = True
            response["install_error"] = install_error
            response["pearl_name"] = data.pearl_name
            if port != data.port:
                response["port_changed"] = True
                response["original_port"] = data.port
            return response

    response = to_dict(server)
    response["install_ran"] = install_ran
    response["install_error"] = install_error
    response["pearl_name"] = effective_data.pearl_name
    if port != data.port:
        response["port_changed"] = True
        response["original_port"] = data.port
    return response

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
                r = await c.get("https://fill.papermc.io/v3/projects/paper")
                data = r.json()
                version_groups = data.get("versions", {})
                collected: list[str] = []
                if isinstance(version_groups, dict):
                    for group_versions in version_groups.values():
                        if isinstance(group_versions, list):
                            collected.extend(
                                version
                                for version in group_versions
                                if isinstance(version, str) and is_stable_minecraft_version(version)
                            )
                versions = unique_versions_desc(collected)
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
    pearl_manifest = read_pearl_manifest(sid, s.name)

    if not has_accepted_eula(sid, s.name):
        if data and data.accept_eula:
            write_eula_accept(sid, s.name)
        else:
            raise HTTPException(400, "EULA acceptance required")

    java = java_cmd(s.version)
    runtime_image = image_for_mc(s.version)
    startup_command_text: str | None = None
    if pearl_manifest and pearl_manifest.get("runtime_image") and (pearl_manifest.get("startup") or s.custom_launch_command):
        cmd_string = normalize_pearl_text(pearl_manifest.get("startup") or s.custom_launch_command)
        cmd_string = (
            cmd_string
            .replace("{jar}", "server.jar")
            .replace("{ram_min}", str(s.ram_min))
            .replace("{ram_max}", str(s.ram_max))
            .replace("{java}", java)
            .replace("{port}", str(s.port))
            .replace("{max_players}", str(s.max_players))
        )
        startup_command_text = cmd_string
        cmd = shlex.split(cmd_string)
        runtime_image = normalize_pearl_text(pearl_manifest.get("runtime_image"), runtime_image)
    else:
        ok, install_error = await ensure_modded_server_layout(s, d)
        if not ok:
            raise HTTPException(status_code=400, detail=install_error or "Failed to prepare server files")

        ensure_runtime_images(client)

        if s.custom_launch_command:
            cmd = s.custom_launch_command.replace("{jar}", "server.jar").replace("{ram_min}", str(s.ram_min))
            cmd = shlex.split(
                cmd
                .replace("{ram_max}", str(s.ram_max))
                .replace("{java}", java)
                .replace("{port}", str(s.port))
                .replace("{max_players}", str(s.max_players))
            )
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
                    f.write(
                        "\n".join([
                            f"-Xmx{s.ram_max}M",
                            f"-Xms{s.ram_min}M",
                            "-XX:+UseG1GC",
                            *terminal_jvm_args(),
                            "",
                        ])
                    )
                ua_rel = container_relative_path(unix_args, d)
                # Forge/NeoForge installers generate unix_args.txt with the correct launch entrypoint.
                cmd = [java, "@user_jvm_args.txt", f"@{ua_rel}", "nogui"]
            elif has_server_jar:
                cmd = [
                    java,
                    f"-Xmx{s.ram_max}M",
                    f"-Xms{s.ram_min}M",
                    *terminal_jvm_args(),
                    "-jar",
                    "server.jar",
                    "nogui",
                ]
            else:
                raise HTTPException(400, "No server files found")

    # Always clean up any leftover container before creating
    try:
        remove_container_if_exists(name, stop_timeout=5)
    except DockerNotFound:
        pass

    try:
        runtime_user = runtime_user_spec()
        is_yolk_runtime = bool(pearl_manifest and is_pterodactyl_yolk_image(runtime_image))
        container_mount_path = "/home/container" if is_yolk_runtime else "/server"
        runtime_env = {"EULA": "TRUE", "HOME": container_mount_path}
        if pearl_manifest and isinstance(pearl_manifest.get("variables"), dict):
            for key, value in pearl_manifest["variables"].items():
                runtime_env[str(key)] = normalize_pearl_text(value)
        runtime_env.setdefault("SERVER_MEMORY", str(s.ram_max))
        runtime_env.setdefault("SERVER_PORT", str(s.port))
        runtime_env.setdefault("SERVER_MAX_PLAYERS", str(s.max_players))
        if is_yolk_runtime and startup_command_text:
            runtime_env["STARTUP"] = startup_command_text
            runtime_env.setdefault("P_SERVER_LOCATION", "none")
            runtime_env.setdefault("TZ", "UTC")
        client.containers.run(
            runtime_image,
            command=None if is_yolk_runtime else cmd,
            name=name,
            detach=True,
            tty=True,
            stdin_open=True,
            volumes={d: {"bind": container_mount_path, "mode": "rw"}},
            ports={"25565/tcp": s.port, "25575/tcp": 25575 + s.id},
            mem_limit=f"{s.ram_max}m",
            memswap_limit=f"{s.ram_max + s.swap_mb}m",
            cpu_period=100000,
            cpu_quota=int(s.cpu_cores * 100000),
            working_dir=container_mount_path,
            environment=runtime_env,
            user=runtime_user,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Docker container. Make sure Docker Desktop is running. {exc}",
        )
    
    s.status = "running"
    db.commit()

    if s.playit_enabled:
        try:
            secret = read_playit_secret_from_disk(s)
            if secret:
                start_playit_container(s)
            if secret:
                tunnel_id, domain, detail = ensure_playit_tunnel(s, secret)
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

    await delete_public_domain_record(db, s)
    cleanup_server_runtime_artifacts(sid)
    d = sdir(sid, s.name)
    remove_server_dir(d)

    db.delete(s)
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
