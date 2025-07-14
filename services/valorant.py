"""Valorant API サービス"""
import httpx
from typing import List, Optional, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

VALORANT_API_BASE_URL = "https://valorant-api.com/v1"


class ValorantAPIService:
    """Valorant APIとの通信を管理するサービス"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=VALORANT_API_BASE_URL,
            timeout=10.0,
            headers={
                "User-Agent": "Fixed-Points-Backend/1.0"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.client.aclose()
    
    async def get_agents(self, language: str = "ja-JP") -> List[Dict[str, Any]]:
        """エージェント一覧を取得
        
        Args:
            language: 言語コード（デフォルト: ja-JP）
            
        Returns:
            エージェント情報のリスト
        """
        try:
            response = await self.client.get(
                "/agents",
                params={
                    "language": language,
                    "isPlayableCharacter": "true"
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == 200:
                agents = data.get("data", [])
                # 必要な情報だけを抽出
                return [
                    {
                        "uuid": agent["uuid"],
                        "displayName": agent["displayName"],
                        "description": agent["description"],
                        "displayIcon": agent["displayIcon"],
                        "role": {
                            "uuid": agent["role"]["uuid"],
                            "displayName": agent["role"]["displayName"]
                        } if agent.get("role") else None
                    }
                    for agent in agents
                ]
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch agents: {e}")
            return []
    
    async def get_maps(self, language: str = "ja-JP") -> List[Dict[str, Any]]:
        """マップ一覧を取得
        
        Args:
            language: 言語コード（デフォルト: ja-JP）
            
        Returns:
            マップ情報のリスト
        """
        try:
            response = await self.client.get(
                "/maps",
                params={"language": language}
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == 200:
                maps = data.get("data", [])
                # 必要な情報だけを抽出（通常のマップのみ）
                return [
                    {
                        "uuid": map_data["uuid"],
                        "displayName": map_data["displayName"],
                        "coordinates": map_data["coordinates"],
                        "displayIcon": map_data["displayIcon"],
                        "listViewIcon": map_data["listViewIcon"],
                        "splash": map_data["splash"]
                    }
                    for map_data in maps
                    if map_data.get("displayName") and map_data.get("coordinates")
                ]
            return []
            
        except Exception as e:
            logger.error(f"Failed to fetch maps: {e}")
            return []


# サービスのインスタンスを返す関数
def get_valorant_service():
    return ValorantAPIService()