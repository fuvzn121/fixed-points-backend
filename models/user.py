from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base
import enum


class AuthProvider(str, enum.Enum):
    EMAIL = "email"
    DISCORD = "discord"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))  # メール認証時のみ
    discord_id = Column(String(255), unique=True, index=True)  # Discord認証時のみ
    discord_username = Column(String(255))  # Discord表示名
    avatar_url = Column(String(500))
    auth_provider = Column(Enum(AuthProvider), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # リレーション
    fixed_points = relationship("FixedPoint", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    auth_tokens = relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")