from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from core.database import Base


class Favorite(Base):
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fixed_point_id = Column(Integer, ForeignKey("fixed_points.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # ユーザーが同じ定点を複数回お気に入りできないようにする
    __table_args__ = (
        UniqueConstraint('user_id', 'fixed_point_id', name='unique_user_fixed_point_favorite'),
    )
    
    # リレーション
    user = relationship("User", back_populates="favorites")
    fixed_point = relationship("FixedPoint", back_populates="favorites")