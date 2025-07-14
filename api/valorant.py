"""Valorant API エンドポイント"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.valorant import valorant_service

router = APIRouter(prefix="/api/valorant", tags=["valorant"])


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_agents(language: str = "ja-JP"):
    """VALORANTのエージェント一覧を取得
    
    Args:
        language: 言語コード（デフォルト: ja-JP）
    
    Returns:
        エージェント情報のリスト
    """
    async with valorant_service as service:
        agents = await service.get_agents(language)
        if not agents:
            raise HTTPException(status_code=503, detail="Failed to fetch agents from Valorant API")
        return agents


@router.get("/maps", response_model=List[Dict[str, Any]])
async def get_maps(language: str = "ja-JP"):
    """VALORANTのマップ一覧を取得
    
    Args:
        language: 言語コード（デフォルト: ja-JP）
    
    Returns:
        マップ情報のリスト
    """
    async with valorant_service as service:
        maps = await service.get_maps(language)
        if not maps:
            raise HTTPException(status_code=503, detail="Failed to fetch maps from Valorant API")
        return maps