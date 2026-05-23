import logging
import re
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models.panel_setting import PanelSetting
from models.server import Server
from models.user import User
from utils.security import get_current_user

router = APIRouter(prefix="/api/servers", tags=["domain-runtime"])
logger = logging.getLogger(__name__)

PUBLIC_DOMAIN_ENABLED_KEY = "public_domain_enabled"
PUBLIC_DOMAIN_SERVICE_URL_KEY = "public_domain_service_url"
PUBLIC_DOMAIN_BASE_DOMAIN_KEY = "public_domain_base_domain"
PUBLIC_DOMAIN_TARGET_HOST_KEY = "public_domain_target_host"
PUBLIC_DOMAIN_SERVICE_TOKEN_KEY = "public_domain_service_token"


class DomainLinkPayload(BaseModel):
    subdomain: str = Field(min_length=1, max_length=63)


def normalize_subdomain(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]", "-", str(value or "").strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    return cleaned[:63]


def normalize_hostname(value: str) -> str:
    return str(value or "").strip().lower().rstrip(".")


def build_public_domain(subdomain: str, base_domain: str) -> str:
    normalized_subdomain = normalize_subdomain(subdomain)
    normalized_base = normalize_hostname(base_domain)
    if not normalized_subdomain or not normalized_base:
        return ""
    return f"{normalized_subdomain}.{normalized_base}"


def get_panel_setting_value(db: Session, key: str, default: str = "") -> str:
    setting = db.query(PanelSetting).filter(PanelSetting.key == key).first()
    if not setting:
        return default
    return str(setting.value or default).strip()


def get_bool_panel_setting(db: Session, key: str, default: bool = False) -> bool:
    raw = get_panel_setting_value(db, key, "1" if default else "0").lower()
    return raw in {"1", "true", "yes", "on"}


def load_public_domain_config(db: Session) -> dict:
    service_enabled = get_bool_panel_setting(db, PUBLIC_DOMAIN_ENABLED_KEY, False)
    service_url = get_panel_setting_value(
        db,
        PUBLIC_DOMAIN_SERVICE_URL_KEY,
        "https://vercel-playit-api.vercel.app/api/cloudflare",
    ).rstrip("/")
    base_domain = normalize_hostname(get_panel_setting_value(db, PUBLIC_DOMAIN_BASE_DOMAIN_KEY, ""))
    target_host = normalize_hostname(get_panel_setting_value(db, PUBLIC_DOMAIN_TARGET_HOST_KEY, ""))
    service_token = get_panel_setting_value(db, PUBLIC_DOMAIN_SERVICE_TOKEN_KEY, "")

    return {
        "service_enabled": service_enabled,
        "service_url": service_url,
        "base_domain": base_domain,
        "target_host": target_host,
        "service_token": service_token,
        "configured": bool(service_enabled and service_url and base_domain),
    }


async def call_public_domain_service(
    config: dict,
    path: str,
    *,
    method: str = "POST",
    payload: Optional[dict] = None,
    params: Optional[dict] = None,
) -> dict:
    if not config.get("service_url"):
        raise HTTPException(503, "Public domain service URL is not configured.")

    headers = {"Content-Type": "application/json"}
    if config.get("service_token"):
        headers["Authorization"] = f"Bearer {config['service_token']}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(
                method.upper(),
                f"{config['service_url']}{path}",
                json=payload,
                params=params,
                headers=headers,
            )
    except Exception as exc:
        logger.warning("Public domain service request failed: %s", exc)
        raise HTTPException(502, "Could not reach the public domain service.") from exc

    try:
        data = response.json()
    except Exception:
        data = {}

    if response.status_code >= 400:
        detail = data.get("detail") or f"Public domain service returned {response.status_code}."
        raise HTTPException(response.status_code if response.status_code < 500 else 502, detail)

    return data


async def delete_public_domain_record(db: Session, server: Server) -> None:
    subdomain = normalize_subdomain(server.public_domain_subdomain or "")
    if not subdomain:
        return

    config = load_public_domain_config(db)
    if not config.get("configured"):
        return

    try:
        await call_public_domain_service(
            config,
            "/srv/delete",
            payload={
                "slug": subdomain,
                "cloudflare_base_domain": config["base_domain"],
                **({"cloudflare_target_host": config["target_host"]} if config["target_host"] else {}),
            },
        )
    except HTTPException as exc:
        logger.warning("Failed to delete public domain record for server %s: %s", server.id, exc.detail)
    except Exception as exc:
        logger.warning("Unexpected public domain delete failure for server %s: %s", server.id, exc)


@router.get("/{server_id}/domain/runtime")
async def get_public_domain_runtime_status(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(404, "Not found")

    config = load_public_domain_config(db)
    subdomain = normalize_subdomain(server.public_domain_subdomain or "")
    domain = server.public_domain or build_public_domain(subdomain, config["base_domain"])

    payload = {
        "service_enabled": config["service_enabled"],
        "configured": config["configured"],
        "service_url": config["service_url"],
        "base_domain": config["base_domain"],
        "enabled": bool(server.public_domain_enabled),
        "subdomain": subdomain,
        "domain": domain,
        "record_exists": False,
        "port": server.port,
        "detail": None,
    }

    if not config["configured"] or not subdomain:
        return payload

    try:
        result = await call_public_domain_service(
            config,
            "/srv/check",
            method="GET",
            params={
                "slug": subdomain,
                "cloudflare_base_domain": config["base_domain"],
            },
        )
        payload["record_exists"] = bool(result.get("exists"))
    except HTTPException as exc:
        payload["detail"] = str(exc.detail)
    except Exception as exc:
        payload["detail"] = str(exc)

    return payload


@router.post("/{server_id}/domain/runtime/link")
async def link_public_domain_runtime(
    server_id: int,
    data: DomainLinkPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(404, "Not found")

    config = load_public_domain_config(db)
    if not config["service_enabled"]:
        raise HTTPException(403, "Public domains are disabled in the admin panel.")
    if not config["configured"]:
        raise HTTPException(503, "Public domain service is not configured yet.")

    subdomain = normalize_subdomain(data.subdomain)
    if not subdomain:
        raise HTTPException(400, "Choose a valid subdomain name.")

    previous_subdomain = normalize_subdomain(server.public_domain_subdomain or "")
    result = await call_public_domain_service(
        config,
        "/srv/create",
        payload={
            "slug": subdomain,
            "port": server.port,
            "cloudflare_base_domain": config["base_domain"],
            **({"cloudflare_target_host": config["target_host"]} if config["target_host"] else {}),
        },
    )

    previous_domain = server.public_domain
    if previous_subdomain and previous_subdomain != subdomain:
        previous_subdomain_value = server.public_domain_subdomain
        previous_domain_value = server.public_domain
        server.public_domain_subdomain = previous_subdomain
        server.public_domain = previous_domain
        await delete_public_domain_record(db, server)
        server.public_domain_subdomain = previous_subdomain_value
        server.public_domain = previous_domain_value

    server.public_domain_enabled = True
    server.public_domain_subdomain = subdomain
    server.public_domain = build_public_domain(subdomain, config["base_domain"])
    db.commit()

    return {
        "status": "linked",
        "action": result.get("action"),
        "enabled": True,
        "subdomain": server.public_domain_subdomain,
        "domain": server.public_domain,
        "record_exists": True,
        "base_domain": config["base_domain"],
        "port": server.port,
    }


@router.post("/{server_id}/domain/runtime/disconnect")
async def disconnect_public_domain_runtime(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    server = db.query(Server).filter(Server.id == server_id, Server.owner_id == current_user.id).first()
    if not server:
        raise HTTPException(404, "Not found")

    await delete_public_domain_record(db, server)

    server.public_domain_enabled = False
    server.public_domain_subdomain = None
    server.public_domain = None
    db.commit()

    return {
        "status": "disconnected",
        "enabled": False,
        "subdomain": "",
        "domain": "",
        "record_exists": False,
        "port": server.port,
    }
