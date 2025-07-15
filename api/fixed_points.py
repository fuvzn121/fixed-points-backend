"""定点API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from core.database import get_db
from core.security import get_current_user
from schemas.fixed_point import (
    FixedPointCreate, 
    FixedPointUpdate, 
    FixedPointResponse, 
    FixedPointListResponse
)
from models.user import User
from models.fixed_point import FixedPoint, FixedPointStep
from models.favorite import Favorite

router = APIRouter(prefix="/api/fixed-points", tags=["fixed-points"])


@router.post("/", response_model=FixedPointResponse, status_code=status.HTTP_201_CREATED)
async def create_fixed_point(
    fixed_point_data: FixedPointCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """定点を作成"""
    # 定点を作成
    fixed_point = FixedPoint(
        user_id=current_user.id,
        title=fixed_point_data.title,
        character_id=fixed_point_data.character_id,
        map_id=fixed_point_data.map_id
    )
    db.add(fixed_point)
    db.flush()  # IDを取得するためにflush
    
    # ステップを作成
    for step_data in fixed_point_data.steps:
        step = FixedPointStep(
            fixed_point_id=fixed_point.id,
            step_order=step_data.step_order,
            image_url=step_data.image_url,
            description=step_data.description
        )
        db.add(step)
    
    db.commit()
    db.refresh(fixed_point)
    
    # レスポンス用にお気に入り情報を追加
    response = FixedPointResponse.model_validate(fixed_point)
    response.favorites_count = 0
    response.is_favorited = False
    
    return response


@router.get("/", response_model=List[FixedPointListResponse])
async def get_fixed_points(
    character_id: Optional[str] = Query(None, description="エージェントIDでフィルタ"),
    map_id: Optional[str] = Query(None, description="マップIDでフィルタ"),
    user_id: Optional[int] = Query(None, description="ユーザーIDでフィルタ"),
    favorited_by: Optional[int] = Query(None, description="お気に入りしたユーザーIDでフィルタ"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """定点一覧を取得"""
    query = db.query(
        FixedPoint.id,
        FixedPoint.user_id,
        FixedPoint.title,
        FixedPoint.character_id,
        FixedPoint.map_id,
        FixedPoint.created_at,
        User.username,
        func.count(Favorite.id).label("favorites_count")
    ).join(User).outerjoin(Favorite)
    
    # フィルタ適用
    if character_id:
        query = query.filter(FixedPoint.character_id == character_id)
    if map_id:
        query = query.filter(FixedPoint.map_id == map_id)
    if user_id:
        query = query.filter(FixedPoint.user_id == user_id)
    if favorited_by:
        query = query.filter(Favorite.user_id == favorited_by)
    
    # グループ化と並び替え
    query = query.group_by(
        FixedPoint.id,
        FixedPoint.user_id,
        FixedPoint.title,
        FixedPoint.character_id,
        FixedPoint.map_id,
        FixedPoint.created_at,
        User.username
    ).order_by(FixedPoint.created_at.desc())
    
    # ページネーション
    fixed_points = query.offset(skip).limit(limit).all()
    
    # レスポンスの構築
    results = []
    for fp in fixed_points:
        is_favorited = False
        if current_user:
            fav = db.query(Favorite).filter(
                and_(
                    Favorite.fixed_point_id == fp.id,
                    Favorite.user_id == current_user.id
                )
            ).first()
            is_favorited = fav is not None
        
        results.append(FixedPointListResponse(
            id=fp.id,
            user_id=fp.user_id,
            title=fp.title,
            character_id=fp.character_id,
            map_id=fp.map_id,
            created_at=fp.created_at,
            username=fp.username,
            favorites_count=fp.favorites_count,
            is_favorited=is_favorited
        ))
    
    return results


@router.get("/{fixed_point_id}", response_model=FixedPointResponse)
async def get_fixed_point(
    fixed_point_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """特定の定点を取得"""
    fixed_point = db.query(FixedPoint).options(
        joinedload(FixedPoint.steps)
    ).filter(FixedPoint.id == fixed_point_id).first()
    
    if not fixed_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed point not found"
        )
    
    # お気に入り数を取得
    favorites_count = db.query(func.count(Favorite.id)).filter(
        Favorite.fixed_point_id == fixed_point_id
    ).scalar()
    
    # 現在のユーザーがお気に入りしているか確認
    is_favorited = False
    if current_user:
        fav = db.query(Favorite).filter(
            and_(
                Favorite.fixed_point_id == fixed_point_id,
                Favorite.user_id == current_user.id
            )
        ).first()
        is_favorited = fav is not None
    
    response = FixedPointResponse.model_validate(fixed_point)
    response.favorites_count = favorites_count
    response.is_favorited = is_favorited
    
    return response


@router.put("/{fixed_point_id}", response_model=FixedPointResponse)
async def update_fixed_point(
    fixed_point_id: int,
    fixed_point_data: FixedPointUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """定点を更新（作成者のみ）"""
    fixed_point = db.query(FixedPoint).filter(FixedPoint.id == fixed_point_id).first()
    
    if not fixed_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed point not found"
        )
    
    if fixed_point.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this fixed point"
        )
    
    # 更新処理
    update_data = fixed_point_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fixed_point, field, value)
    
    db.commit()
    db.refresh(fixed_point)
    
    # レスポンス用にお気に入り情報を追加
    favorites_count = db.query(func.count(Favorite.id)).filter(
        Favorite.fixed_point_id == fixed_point_id
    ).scalar()
    
    response = FixedPointResponse.model_validate(fixed_point)
    response.favorites_count = favorites_count
    response.is_favorited = False  # 自分の投稿
    
    return response


@router.delete("/{fixed_point_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fixed_point(
    fixed_point_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """定点を削除（作成者のみ）"""
    fixed_point = db.query(FixedPoint).filter(FixedPoint.id == fixed_point_id).first()
    
    if not fixed_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed point not found"
        )
    
    if fixed_point.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this fixed point"
        )
    
    db.delete(fixed_point)
    db.commit()


@router.post("/{fixed_point_id}/favorite", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    fixed_point_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """定点をお気に入りに追加"""
    # 定点の存在確認
    fixed_point = db.query(FixedPoint).filter(FixedPoint.id == fixed_point_id).first()
    if not fixed_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fixed point not found"
        )
    
    # 既にお気に入りしているか確認
    existing_favorite = db.query(Favorite).filter(
        and_(
            Favorite.fixed_point_id == fixed_point_id,
            Favorite.user_id == current_user.id
        )
    ).first()
    
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already favorited"
        )
    
    # お気に入り追加
    favorite = Favorite(
        user_id=current_user.id,
        fixed_point_id=fixed_point_id
    )
    db.add(favorite)
    db.commit()
    
    return {"message": "Added to favorites"}


@router.delete("/{fixed_point_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    fixed_point_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """定点をお気に入りから削除"""
    favorite = db.query(Favorite).filter(
        and_(
            Favorite.fixed_point_id == fixed_point_id,
            Favorite.user_id == current_user.id
        )
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    db.delete(favorite)
    db.commit()