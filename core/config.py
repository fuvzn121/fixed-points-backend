from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # アプリケーション設定
    APP_NAME: str = "Fixed Points API"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # データベース設定
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fixed_points"
    
    # JWT設定
    JWT_SECRET: str = "your-secret-key-here"  # 本番環境では環境変数から取得
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS設定
    FRONTEND_URL: str = "http://localhost:5173"
    
    # Discord OAuth設定
    DISCORD_CLIENT_ID: Optional[str] = None
    DISCORD_CLIENT_SECRET: Optional[str] = None
    DISCORD_REDIRECT_URI: str = "http://localhost:8000/api/auth/discord/callback"
    
    # Riot API設定
    RIOT_API_KEY: Optional[str] = None
    
    # Cloudinary設定（画像アップロード用）
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()