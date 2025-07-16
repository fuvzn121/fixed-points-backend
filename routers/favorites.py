from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from core.database import get_db
from core.security import get_current_user
from models.user import User
from models.favorite import Favorite
from models.fixed_point import FixedPoint
from schemas.favorite import FavoriteResponse, FavoriteCreate

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.post("/", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    favorite_data: FavoriteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """お気に入りを追加"""
    # 定点が存在するかチェック
    fixed_point = db.query(FixedPoint).filter(FixedPoint.id == favorite_data.fixed_point_id).first()
    if not fixed_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed point not found"
        )
    
    # 既にお気に入りに追加されているかチェック
    existing_favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.fixed_point_id == favorite_data.fixed_point_id
    ).first()
    
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already favorited"
        )
    
    # お気に入りを作成
    favorite = Favorite(
        user_id=current_user.id,
        fixed_point_id=favorite_data.fixed_point_id
    )
    
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    
    return favorite


@router.delete("/{fixed_point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    fixed_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """お気に入りを削除"""
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.fixed_point_id == fixed_point_id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    db.delete(favorite)
    db.commit()


@router.get("/", response_model=List[FavoriteResponse])
async def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自分のお気に入り一覧を取得"""
    favorites = db.query(Favorite).filter(
        Favorite.user_id == current_user.id
    ).order_by(Favorite.created_at.desc()).all()
    
    return favorites


@router.get("/check/{fixed_point_id}")
async def check_favorite_status(
    fixed_point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """特定の定点のお気に入り状態をチェック"""
    favorite = db.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.fixed_point_id == fixed_point_id
    ).first()
    
    return {"is_favorited": favorite is not None}