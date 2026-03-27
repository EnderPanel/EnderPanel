from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func
from typing import Optional
from database import Base

class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(100))
    owner_id: Mapped[int] = Column(Integer, ForeignKey("users.id"))
    status: Mapped[str] = Column(String(20), default="stopped")
    server_type: Mapped[str] = Column(String(20), default="paper")
    port: Mapped[int] = Column(Integer, default=25565)
    max_players: Mapped[int] = Column(Integer, default=20)
    version: Mapped[str] = Column(String(20), default="1.21.11")
    motd: Mapped[str] = Column(String(255), default="A Minecraft Server")
    ram_min: Mapped[int] = Column(Integer, default=512)
    ram_max: Mapped[int] = Column(Integer, default=1024)
    cpu_cores: Mapped[int] = Column(Integer, default=1)
    custom_launch_command: Mapped[Optional[str]] = Column(Text, nullable=True)
    avatar: Mapped[Optional[str]] = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
