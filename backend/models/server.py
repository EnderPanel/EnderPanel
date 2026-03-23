from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="stopped")
    server_type = Column(String(20), default="paper")
    port = Column(Integer, default=25565)
    max_players = Column(Integer, default=20)
    version = Column(String(20), default="1.21.11")
    motd = Column(String(255), default="A Minecraft Server")
    ram_min = Column(Integer, default=512)
    ram_max = Column(Integer, default=1024)
    cpu_cores = Column(Integer, default=1)
    custom_launch_command = Column(Text, nullable=True)
    avatar = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
