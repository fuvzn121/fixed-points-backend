"""認証関連のスキーマ"""
from pydantic import BaseModel, Field
from pydantic import EmailStr as PydanticEmailStr
from typing import Optional
from datetime import datetime

# Pydantic v2用のエイリアス
EmailStr = PydanticEmailStr


class UserRegister(BaseModel):
    """ユーザー登録リクエスト"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """ログインリクエスト"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """認証トークンレスポンス"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """トークンペイロードデータ"""
    user_id: int
    username: str
    email: Optional[str] = None


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    id: int
    username: str
    email: Optional[str]
    auth_provider: str
    avatar_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True