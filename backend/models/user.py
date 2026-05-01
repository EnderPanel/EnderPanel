from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import Mapped
from typing import Optional
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    username: Mapped[str] = Column(String(50), unique=True, index=True)
    email: Mapped[str] = Column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = Column(String(255))
    is_admin: Mapped[bool] = Column(Boolean, default=False)
    avatar: Mapped[Optional[str]] = Column(String(255), nullable=True)
    totp_secret: Mapped[Optional[str]] = Column(String(32), nullable=True)
    playit_agent_id: Mapped[Optional[str]] = Column(String(128), nullable=True)
    _playit_agent_secret: Mapped[Optional[str]] = Column("playit_agent_secret", String(255), nullable=True)

    @property
    def playit_agent_secret(self) -> Optional[str]:
        from utils.security import decrypt_secret

        return decrypt_secret(self._playit_agent_secret)

    @playit_agent_secret.setter
    def playit_agent_secret(self, value: Optional[str]) -> None:
        from utils.security import encrypt_secret

        self._playit_agent_secret = encrypt_secret(value)
