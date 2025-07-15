"""認証サービス"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import or_
import secrets

from core.config import settings
from models.user import User, AuthProvider
from models.auth_token import AuthToken
from schemas.auth import TokenData

# パスワードハッシュ化の設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """認証関連の処理を管理するサービス"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """パスワードの検証"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """パスワードのハッシュ化"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """アクセストークンの作成"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """リフレッシュトークンの作成"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """トークンのデコード"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            user_id: int = payload.get("user_id")
            username: str = payload.get("username")
            email: str = payload.get("email")
            if user_id is None or username is None:
                return None
            return TokenData(user_id=user_id, username=username, email=email)
        except JWTError:
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """ユーザー認証"""
        user = db.query(User).filter(
            User.email == email,
            User.auth_provider == AuthProvider.EMAIL
        ).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> User:
        """新規ユーザー作成"""
        hashed_password = AuthService.get_password_hash(password)
        user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            auth_provider=AuthProvider.EMAIL
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """メールアドレスでユーザーを取得"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """ユーザー名でユーザーを取得"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def user_exists(db: Session, username: str, email: str) -> bool:
        """ユーザーの存在確認"""
        return db.query(User).filter(
            or_(User.username == username, User.email == email)
        ).first() is not None