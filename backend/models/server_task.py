from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped
from database import Base
from sqlalchemy.sql import func


class ServerTask(Base):
    __tablename__ = "server_tasks"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    server_id: Mapped[int] = Column(Integer, ForeignKey("servers.id"), index=True, nullable=False)
    name: Mapped[str] = Column(String(100), nullable=False)
    action: Mapped[str] = Column(String(20), nullable=False)
    interval_minutes: Mapped[int] = Column(Integer, nullable=False, default=60)
    schedule_mode: Mapped[str] = Column(String(20), nullable=False, default="interval")
    run_time: Mapped[str | None] = Column(String(5), nullable=True)
    run_days: Mapped[str | None] = Column(String(32), nullable=True)
    enabled: Mapped[bool] = Column(Boolean, nullable=False, default=True)
    command: Mapped[str | None] = Column(Text, nullable=True)
    last_status: Mapped[str | None] = Column(String(20), nullable=True)
    last_error: Mapped[str | None] = Column(Text, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
