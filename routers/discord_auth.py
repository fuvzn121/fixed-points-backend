from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

from core.database import get_db
from core.config import settings
from models.user import User, AuthProvider
from models.auth_token import AuthToken
from services.auth import AuthService

router = APIRouter(prefix="/api/auth/discord", tags=["Discord OAuth"])

# PKCE用のstate管理（本番環境ではRedisなどを使用）
state_store = {}

@router.get("/login")
async def discord_login():
    """Discord OAuth認証開始"""
    if not settings.DISCORD_CLIENT_ID:
        raise HTTPException(status_code=501, detail="Discord OAuth is not configured. Please set DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET in environment variables.")
    
    # PKCEのstate生成
    state = secrets.token_urlsafe(32)
    state_store[state] = {"timestamp": datetime.now(timezone.utc)}
    
    # Discord OAuth認証URL
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={settings.DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify%20email"
        f"&state={state}"
    )
    
    return {"auth_url": discord_auth_url}

@router.get("/callback")
async def discord_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """Discord OAuth認証コールバック"""
    if not settings.DISCORD_CLIENT_ID or not settings.DISCORD_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Discord OAuth is not configured")
    
    # state検証
    if state not in state_store:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    # state使用後は削除
    del state_store[state]
    
    # アクセストークンの交換
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.DISCORD_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        token_data = token_response.json()
        access_token = token_data["access_token"]
        
        # ユーザー情報の取得
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        user_data = user_response.json()
        
        # ユーザー情報の処理
        discord_id = user_data["id"]
        username = user_data["username"]
        email = user_data.get("email")
        avatar_url = None
        
        if user_data.get("avatar"):
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{user_data['avatar']}.png"
        
        # 既存ユーザーの確認（Discord IDで検索）
        existing_user = db.query(User).filter(
            User.discord_id == discord_id
        ).first()
        
        if existing_user:
            # 既存ユーザーの情報更新
            # ユーザー名の重複チェック（自分以外のユーザーで）
            username_exists = db.query(User).filter(
                User.username == username,
                User.id != existing_user.id
            ).first()
            if username_exists:
                # ユーザー名が重複している場合、Discord IDをサフィックスとして追加
                username = f"{username}_{discord_id[:8]}"
            
            existing_user.username = username
            existing_user.email = email
            existing_user.avatar_url = avatar_url
            user = existing_user
        else:
            # ユーザー名の重複チェック
            username_exists = db.query(User).filter(User.username == username).first()
            if username_exists:
                # ユーザー名が重複している場合、Discord IDをサフィックスとして追加
                username = f"{username}_{discord_id[:8]}"
            
            # 新規ユーザー作成
            user = User(
                username=username,
                email=email,
                discord_id=discord_id,
                auth_provider=AuthProvider.DISCORD,
                avatar_url=avatar_url
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # JWTトークンの生成
        access_token_jwt = AuthService.create_access_token(data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        })
        refresh_token_jwt = AuthService.create_refresh_token(data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        })
        
        # リフレッシュトークンをデータベースに保存
        # リフレッシュトークンのハッシュ化
        token_hash = hashlib.sha256(refresh_token_jwt.encode()).hexdigest()
        
        auth_token = AuthToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(auth_token)
        db.commit()
        
        # フロントエンドにリダイレクト（トークンをクエリパラメータで渡す）
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token_jwt}&refresh_token={refresh_token_jwt}"
        
        return RedirectResponse(url=frontend_url)

@router.post("/revoke")
async def revoke_discord_token(
    discord_token: str,
    db: Session = Depends(get_db)
):
    """Discord OAuth トークンの取り消し"""
    if not settings.DISCORD_CLIENT_ID or not settings.DISCORD_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Discord OAuth is not configured")
    
    async with httpx.AsyncClient() as client:
        revoke_response = await client.post(
            "https://discord.com/api/oauth2/token/revoke",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "token": discord_token
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if revoke_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to revoke token")
    
    return {"message": "Token revoked successfully"}