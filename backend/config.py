import base64
import hashlib
import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'mcpanel.db')}"


def _read_or_create_secret(path: str, env_name: str, generator) -> str:
    env_value = os.getenv(env_name, "").strip()
    if env_value:
        return env_value

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as secret_file:
            value = secret_file.read().strip()
            if value:
                return value

    value = generator()
    with open(path, "w", encoding="utf-8") as secret_file:
        secret_file.write(value)
    os.chmod(path, 0o600)
    return value


SECRET_KEY = _read_or_create_secret(
    os.path.join(BASE_DIR, ".secret_key"),
    "SECRET_KEY",
    lambda: secrets.token_urlsafe(48),
)
DATA_ENCRYPTION_KEY = _read_or_create_secret(
    os.path.join(BASE_DIR, ".data_encryption_key"),
    "DATA_ENCRYPTION_KEY",
    lambda: base64.urlsafe_b64encode(hashlib.sha256(secrets.token_bytes(32)).digest()).decode("ascii"),
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

SERVERS_DIR = os.path.join(BASE_DIR, "servers")
AVATARS_DIR = os.path.join(BASE_DIR, "avatars")

PLAYIT_PARTNER_API_KEY = os.getenv("PLAYIT_PARTNER_API_KEY", "").strip()
PLAYIT_VARIANT_ID = os.getenv("PLAYIT_VARIANT_ID", "").strip()
PLAYIT_AGENT_NAME = os.getenv("PLAYIT_AGENT_NAME", "EnderPanel").strip() or "EnderPanel"
PLAYIT_AGENT_IMAGE = os.getenv("PLAYIT_AGENT_IMAGE", "ghcr.io/playit-cloud/playit-agent:latest").strip()
PLAYIT_SETUP_URL = "https://playit.gg/l/setup-third-party"
PLAYIT_DASHBOARD_URL = "https://playit.gg/account/agents"

os.makedirs(AVATARS_DIR, exist_ok=True)
