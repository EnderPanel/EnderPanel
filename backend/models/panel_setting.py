from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import Mapped
from sqlalchemy.sql import func

from database import Base


class PanelSetting(Base):
    __tablename__ = "panel_settings"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    key: Mapped[str] = Column(String(100), unique=True, nullable=False, index=True)
    value: Mapped[str] = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
