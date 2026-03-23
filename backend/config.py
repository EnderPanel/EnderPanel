import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'mcpanel.db')}"

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

SERVERS_DIR = os.path.join(BASE_DIR, "servers")
AVATARS_DIR = os.path.join(BASE_DIR, "avatars")

os.makedirs(AVATARS_DIR, exist_ok=True)
