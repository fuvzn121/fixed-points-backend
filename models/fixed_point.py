from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class FixedPoint(Base):
    __tablename__ = "fixed_points"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    character_id = Column(String(50), nullable=False, index=True)  # Riot APIのエージェントID
    map_id = Column(String(50), nullable=False, index=True)  # Riot APIのマップID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # リレーション
    user = relationship("User", back_populates="fixed_points")
    steps = relationship("FixedPointStep", back_populates="fixed_point", cascade="all, delete-orphan", order_by="FixedPointStep.step_order")
    favorites = relationship("Favorite", back_populates="fixed_point", cascade="all, delete-orphan")


class FixedPointStep(Base):
    __tablename__ = "fixed_point_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    fixed_point_id = Column(Integer, ForeignKey("fixed_points.id"), nullable=False)
    step_order = Column(Integer, nullable=False)  # 1-5
    image_url = Column(String(500))
    description = Column(Text)
    # マップ座標情報
    position_x = Column(Float)  # 開始位置のX座標（0-1の正規化座標）
    position_y = Column(Float)  # 開始位置のY座標（0-1の正規化座標）
    skill_position_x = Column(Float)  # スキル着弾地点のX座標（0-1の正規化座標）
    skill_position_y = Column(Float)  # スキル着弾地点のY座標（0-1の正規化座標）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # リレーション
    fixed_point = relationship("FixedPoint", back_populates="steps")