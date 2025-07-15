"""定点関連のスキーマ"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class FixedPointStepBase(BaseModel):
    """定点ステップの基本スキーマ"""
    step_order: int = Field(..., ge=1, le=5, description="ステップの順番（1-5）")
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    # マップ上の座標情報
    position_x: Optional[float] = Field(None, description="マップ上のX座標（0-1の正規化座標）")
    position_y: Optional[float] = Field(None, description="マップ上のY座標（0-1の正規化座標）")
    skill_position_x: Optional[float] = Field(None, description="スキル着弾地点のX座標（0-1の正規化座標）")
    skill_position_y: Optional[float] = Field(None, description="スキル着弾地点のY座標（0-1の正規化座標）")


class FixedPointStepCreate(FixedPointStepBase):
    """定点ステップ作成スキーマ"""
    pass


class FixedPointStepUpdate(BaseModel):
    """定点ステップ更新スキーマ"""
    image_url: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None


class FixedPointStepResponse(FixedPointStepBase):
    """定点ステップレスポンススキーマ"""
    id: int
    fixed_point_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class FixedPointBase(BaseModel):
    """定点の基本スキーマ"""
    title: str = Field(..., min_length=1, max_length=255)
    character_id: str = Field(..., max_length=50, description="Valorantエージェント ID")
    map_id: str = Field(..., max_length=50, description="ValorantマップID")


class FixedPointCreate(FixedPointBase):
    """定点作成スキーマ"""
    steps: List[FixedPointStepCreate] = Field(..., min_length=1, max_length=5)


class FixedPointUpdate(BaseModel):
    """定点更新スキーマ"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    character_id: Optional[str] = Field(None, max_length=50)
    map_id: Optional[str] = Field(None, max_length=50)


class FixedPointResponse(FixedPointBase):
    """定点レスポンススキーマ"""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    steps: List[FixedPointStepResponse]
    favorites_count: int = 0
    is_favorited: bool = False

    class Config:
        from_attributes = True


class FixedPointListResponse(BaseModel):
    """定点一覧レスポンススキーマ"""
    id: int
    user_id: int
    title: str
    character_id: str
    map_id: str
    created_at: datetime
    favorites_count: int = 0
    is_favorited: bool = False
    username: str

    class Config:
        from_attributes = True