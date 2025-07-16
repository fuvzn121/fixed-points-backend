from pydantic import BaseModel
from datetime import datetime


class FavoriteBase(BaseModel):
    """お気に入りの基底モデル"""
    fixed_point_id: int


class FavoriteCreate(FavoriteBase):
    """お気に入り作成用モデル"""
    pass


class FavoriteResponse(FavoriteBase):
    """お気に入りレスポンス用モデル"""
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True