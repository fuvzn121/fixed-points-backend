"""Valorant API エンドポイント"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from services.valorant import get_valorant_service
from services.image_cache import image_cache_service

router = APIRouter(prefix="/api/valorant", tags=["valorant"])


@router.get("/agents", response_model=List[Dict[str, Any]])
async def get_agents(language: str = "ja-JP"):
    """VALORANTのエージェント一覧を取得（画像はキャッシュ済みのローカルパスに変換）
    
    Args:
        language: 言語コード（デフォルト: ja-JP）
    
    Returns:
        エージェント情報のリスト（画像URLはローカルパス）
    """
    service = get_valorant_service()
    async with service:
        agents = await service.get_agents(language)
        if not agents:
            raise HTTPException(status_code=503, detail="Failed to fetch agents from Valorant API")
        
        # 画像をキャッシュして、URLをローカルパスに置き換える
        for agent in agents:
            if agent.get('displayIcon'):
                cached_path = await image_cache_service.cache_agent_image(
                    agent['uuid'], 
                    agent['displayIcon']
                )
                if cached_path:
                    agent['displayIcon'] = cached_path
        
        return agents


@router.get("/maps", response_model=List[Dict[str, Any]])
async def get_maps(language: str = "ja-JP"):
    """VALORANTのマップ一覧を取得（画像はキャッシュ済みのローカルパスに変換）
    
    Args:
        language: 言語コード（デフォルト: ja-JP）
    
    Returns:
        マップ情報のリスト（画像URLはローカルパス）
    """
    service = get_valorant_service()
    async with service:
        maps = await service.get_maps(language)
        if not maps:
            raise HTTPException(status_code=503, detail="Failed to fetch maps from Valorant API")
        
        # 画像をキャッシュして、URLをローカルパスに置き換える
        for map_data in maps:
            if map_data.get('displayIcon') and map_data.get('splash'):
                cached_paths = await image_cache_service.cache_map_images(
                    map_data['uuid'],
                    map_data['displayIcon'],
                    map_data['splash']
                )
                if cached_paths.get('displayIcon'):
                    map_data['displayIcon'] = cached_paths['displayIcon']
                if cached_paths.get('splash'):
                    map_data['splash'] = cached_paths['splash']
        
        return maps