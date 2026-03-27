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
