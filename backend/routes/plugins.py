import os
import json
import httpx
import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.server import Server
from utils.security import get_current_user
from config import SERVERS_DIR

router = APIRouter(prefix="/api/servers/{server_id}/mods", tags=["mods"])

MODRINTH_API = "https://api.modrinth.com/v2"

def sanitize_name(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def get_server_dir(server_id: int, server_name: str = None):
    if server_name:
        return os.path.join(SERVERS_DIR, f"{server_id}-{sanitize_name(server_name)}")
    for folder in os.listdir(SERVERS_DIR):
        if folder.startswith(f"{server_id}-"):
            return os.path.join(SERVERS_DIR, folder)
    return os.path.join(SERVERS_DIR, str(server_id))


def safe_child_path(root: str, filename: str | None) -> str:
    name = (filename or "").replace("\\", "/")
    if name != os.path.basename(name) or name in ("", ".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename")

    root_real = os.path.realpath(root)
    full_path = os.path.realpath(os.path.join(root_real, name))
    try:
        inside_root = os.path.commonpath([root_real, full_path]) == root_real
    except ValueError:
        inside_root = False
    if not inside_root:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return full_path


def get_modrinth_config(server_type: str):
    server_type = server_type.lower()
    if server_type in ("paper", "spigot", "bukkit"):
        return "plugin", ["paper", "spigot", "bukkit"], "plugins"
    elif server_type == "fabric":
        return "mod", ["fabric"], "mods"
    elif server_type == "forge":
        return "mod", ["forge"], "mods"
    elif server_type == "neoforge":
        return "mod", ["neoforge"], "mods"
    else:
        raise HTTPException(status_code=400, detail=f"Server type '{server_type}' does not support mods/plugins")

def get_metadata_path(server_id: int, server_name: str) -> str:
    return os.path.join(get_server_dir(server_id, server_name), "mcpanel_mods.json")

def load_metadata(server_id: int, server_name: str) -> dict:
    path = get_metadata_path(server_id, server_name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {"mods": {}}

def save_metadata(server_id: int, server_name: str, data: dict):
    path = get_metadata_path(server_id, server_name)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/search")
async def search_mods(server_id: int, query: str = "", page: int = 1, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    project_type, loaders, _ = get_modrinth_config(server.server_type)

    async with httpx.AsyncClient() as client:
        offset = (page - 1) * 20
        facets = f'[["project_type:{project_type}"]'
        if loaders:
            loader_or = ",".join(f'"categories:{l}"' for l in loaders)
            facets += f',[{loader_or}]'
        facets += ']'

        loaders_param = "[" + ",".join(f'"{l}"' for l in loaders) + "]"
        response = await client.get(
            f"{MODRINTH_API}/search",
            params={"query": query, "facets": facets, "limit": 20, "offset": offset}
        )
        data = response.json()
        data["server_type"] = server.server_type
        data["project_type"] = project_type
        data["mc_version"] = server.version
        data["loader"] = loaders[0]
        return data

@router.get("/installed")
def list_installed(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    _, _, install_dir = get_modrinth_config(server.server_type)
    mods_dir = os.path.join(get_server_dir(server_id, server.name), install_dir)
    if not os.path.exists(mods_dir):
        return []

    metadata = load_metadata(server_id, server.name)
    mods = []
    for file in os.listdir(mods_dir):
        if file.endswith(".jar"):
            mod_info = metadata.get("mods", {}).get(file, {})
            mods.append({
                "name": file,
                "size": os.path.getsize(os.path.join(mods_dir, file)),
                "project_id": mod_info.get("project_id"),
                "project_title": mod_info.get("project_title"),
                "version": mod_info.get("version"),
                "installed_at": mod_info.get("installed_at")
            })
    return mods

@router.get("/updates/check")
async def check_updates(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    metadata = load_metadata(server_id, server.name)
    mods = metadata.get("mods", {})
    
    if not mods:
        return {"updates": []}

    _, loaders, _ = get_modrinth_config(server.server_type)
    loaders_param = "[" + ",".join(f'"{l}"' for l in loaders) + "]"

    updates = []
    async with httpx.AsyncClient() as client:
        for filename, info in mods.items():
            project_id = info.get("project_id")
            current_version = info.get("version")
            
            if not project_id:
                continue

            try:
                versions_response = await client.get(
                    f"{MODRINTH_API}/project/{project_id}/version",
                    params={"game_versions": f'["{server.version}"]', "loaders": loaders_param}
                )
                versions = versions_response.json()

                if versions:
                    latest = versions[0]
                    if latest["version_number"] != current_version:
                        updates.append({
                            "filename": filename,
                            "project_id": project_id,
                            "project_title": info.get("project_title", project_id),
                            "current_version": current_version,
                            "latest_version": latest["version_number"],
                            "latest_version_id": latest["id"],
                            "version_type": latest["version_type"]
                        })
            except Exception as e:
                print(f"Error checking updates for {project_id}: {e}")

    return {"updates": updates, "server_version": server.version}

@router.post("/updates/update-all")
async def update_all(server_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    check_result = await check_updates(server_id, db, current_user)
    updates = check_result.get("updates", [])
    
    results = []
    for update in updates:
        try:
            result = await update_mod(server_id, update["filename"], db, current_user)
            results.append(result)
        except Exception as e:
            results.append({"status": "error", "filename": update["filename"], "error": str(e)})

    return {"results": results, "total": len(updates)}

@router.post("/link/{filename}")
async def link_modrinth(server_id: int, filename: str, project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    if "modrinth.com" in project_id:
        parts = project_id.rstrip("/").split("/")
        project_id = parts[-1] if parts else project_id

    _, _, install_dir = get_modrinth_config(server.server_type)
    file_path = safe_child_path(os.path.join(get_server_dir(server_id, server.name), install_dir), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Plugin file not found")

    async with httpx.AsyncClient() as client:
        try:
            project_response = await client.get(f"{MODRINTH_API}/project/{project_id}")
            project = project_response.json()
            project_title = project.get("title", project_id)
        except:
            raise HTTPException(status_code=404, detail="Modrinth project not found")

        _, loaders, _ = get_modrinth_config(server.server_type)
        loaders_param = "[" + ",".join(f'"{l}"' for l in loaders) + "]"
        
        versions_response = await client.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params={"game_versions": f'["{server.version}"]', "loaders": loaders_param}
        )
        versions = versions_response.json()

    installed_version = "unknown"
    filename_lower = filename.lower()
    for v in versions:
        ver_num = v["version_number"].lower()
        if ver_num in filename_lower or filename_lower.replace(".jar", "").endswith(ver_num):
            installed_version = v["version_number"]
            break
    
    if installed_version == "unknown":
        import re
        match = re.search(r'(\d+\.\d+\.\d+)', filename)
        if match:
            installed_version = match.group(1)

    installed_version_id = None
    installed_date = None
    for v in versions:
        if v["version_number"] == installed_version:
            installed_version_id = v["id"]
            installed_date = v["date_published"]
            break

    metadata = load_metadata(server_id, server.name)
    metadata.setdefault("mods", {})[filename] = {
        "project_id": project_id,
        "project_title": project_title,
        "version": installed_version,
        "version_id": installed_version_id,
        "installed_at": installed_date
    }
    save_metadata(server_id, server.name, metadata)

    return {"status": "linked", "filename": filename, "project_id": project_id, "project_title": project_title, "version": installed_version}

@router.post("/update/{filename}")
async def update_mod(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    metadata = load_metadata(server_id, server.name)
    mod_info = metadata.get("mods", {}).get(filename)
    
    if not mod_info:
        raise HTTPException(status_code=404, detail="Mod metadata not found")

    project_id = mod_info.get("project_id")
    if not project_id:
        raise HTTPException(status_code=400, detail="No Modrinth project ID stored for this mod")

    _, loaders, install_dir = get_modrinth_config(server.server_type)
    loaders_param = "[" + ",".join(f'"{l}"' for l in loaders) + "]"
    mods_dir = os.path.join(get_server_dir(server_id, server.name), install_dir)

    async with httpx.AsyncClient() as client:
        versions_response = await client.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params={"game_versions": f'["{server.version}"]', "loaders": loaders_param}
        )
        versions = versions_response.json()

        if not versions:
            raise HTTPException(status_code=404, detail="No compatible versions found")

        latest = versions[0]

        old_file_path = safe_child_path(mods_dir, filename)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

        for file in latest["files"]:
            if file["primary"]:
                download_response = await client.get(file["url"])
                file_path = safe_child_path(mods_dir, file["filename"])
                with open(file_path, "wb") as f:
                    f.write(download_response.content)

                if filename in metadata.get("mods", {}):
                    del metadata["mods"][filename]
                
                metadata.setdefault("mods", {})[file["filename"]] = {
                    "project_id": project_id,
                    "project_title": mod_info.get("project_title", project_id),
                    "version": latest["version_number"],
                    "version_id": latest["id"],
                    "installed_at": latest["date_published"]
                }
                save_metadata(server_id, server.name, metadata)

                return {
                    "status": "updated",
                    "old_filename": filename,
                    "new_filename": file["filename"],
                    "old_version": mod_info.get("version"),
                    "new_version": latest["version_number"],
                    "project_title": mod_info.get("project_title", project_id)
                }

    raise HTTPException(status_code=400, detail="No primary file found")

@router.get("/{project_id}/versions")
async def get_mod_versions(server_id: int, project_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    _, loaders, _ = get_modrinth_config(server.server_type)
    loaders_param = "[" + ",".join(f'"{l}"' for l in loaders) + "]"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MODRINTH_API}/project/{project_id}/version",
            params={"game_versions": f'["{server.version}"]', "loaders": loaders_param}
        )
        versions = response.json() if response.status_code == 200 else []

        if not versions:
            fallback = await client.get(
                f"{MODRINTH_API}/project/{project_id}/version",
                params={"loaders": loaders_param}
            )
            versions = fallback.json() if fallback.status_code == 200 else []

        compatible = []
        for v in versions:
            compatible.append({
                "version_number": v["version_number"],
                "version_type": v["version_type"],
                "date_published": v["date_published"],
                "files": [{"filename": f["filename"], "size": f["size"], "primary": f["primary"]} for f in v["files"]],
                "id": v["id"],
                "loaders": v.get("loaders", [])
            })

        return {"server_version": server.version, "server_type": server.server_type, "versions": compatible}

@router.post("/install/{project_id}")
async def install_mod(server_id: int, project_id: str, version_id: str = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    import subprocess as _sp
    _, loaders, install_dir = get_modrinth_config(server.server_type)
    loaders_param = "[" + ",".join(f'"{l}"' for l in loaders) + "]"
    mods_dir = os.path.join(get_server_dir(server_id, server.name), install_dir)
    os.makedirs(mods_dir, exist_ok=True)
    _sp.run(["sudo", "chmod", "-R", "777", mods_dir], check=False, capture_output=True)

    async with httpx.AsyncClient() as client:
        project_response = await client.get(f"{MODRINTH_API}/project/{project_id}")
        project = project_response.json()
        project_title = project.get("title", project_id)

        if version_id:
            version_response = await client.get(f"{MODRINTH_API}/version/{version_id}")
            version = version_response.json()
        else:
            versions_response = await client.get(
                f"{MODRINTH_API}/project/{project_id}/version",
                params={"game_versions": f'["{server.version}"]', "loaders": loaders_param}
            )
            versions = versions_response.json()

            if not versions:
                raise HTTPException(status_code=404, detail=f"No compatible versions found for {server.server_type} {server.version}")

            version = versions[0]

        for file in version["files"]:
            if file["primary"]:
                download_response = await client.get(file["url"])
                file_path = safe_child_path(mods_dir, file["filename"])
                with open(file_path, "wb") as f:
                    f.write(download_response.content)

                metadata = load_metadata(server_id, server.name)
                metadata.setdefault("mods", {})[file["filename"]] = {
                    "project_id": project_id,
                    "project_title": project_title,
                    "version": version["version_number"],
                    "version_id": version["id"],
                    "installed_at": version["date_published"]
                }
                save_metadata(server_id, server.name, metadata)

                return {
                    "status": "installed",
                    "filename": file["filename"],
                    "version": version["version_number"],
                    "project_title": project_title,
                    "server_version": server.version,
                    "server_type": server.server_type
                }

    raise HTTPException(status_code=400, detail="No primary file found")

@router.delete("/{filename}")
def uninstall_mod(server_id: int, filename: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    _, _, install_dir = get_modrinth_config(server.server_type)
    file_path = safe_child_path(os.path.join(get_server_dir(server_id, server.name), install_dir), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Mod/Plugin not found")

    os.remove(file_path)

    metadata = load_metadata(server_id, server.name)
    if filename in metadata.get("mods", {}):
        del metadata["mods"][filename]
        save_metadata(server_id, server.name, metadata)

    return {"status": "uninstalled"}
