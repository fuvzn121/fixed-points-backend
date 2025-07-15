"""画像キャッシュサービス"""
import os
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ImageCacheService:
    """Valorant画像のローカルキャッシュを管理"""
    
    def __init__(self):
        self.static_dir = Path("static")
        self.agents_dir = self.static_dir / "images" / "agents"
        self.maps_dir = self.static_dir / "images" / "maps"
        
        # ディレクトリが存在することを確認
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self.maps_dir.mkdir(parents=True, exist_ok=True)
    
    async def download_image(self, url: str, filepath: Path) -> bool:
        """画像をダウンロードして保存"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        logger.info(f"Downloaded image: {filepath}")
                        return True
                    else:
                        logger.error(f"Failed to download image from {url}: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return False
    
    async def cache_agent_image(self, agent_uuid: str, image_url: str) -> Optional[str]:
        """エージェント画像をキャッシュ"""
        filename = f"{agent_uuid}.png"
        filepath = self.agents_dir / filename
        
        # 既にキャッシュされている場合はそのパスを返す
        if filepath.exists():
            return f"/static/images/agents/{filename}"
        
        # ダウンロードしてキャッシュ
        success = await self.download_image(image_url, filepath)
        if success:
            return f"/static/images/agents/{filename}"
        return None
    
    async def cache_map_images(self, map_uuid: str, display_icon_url: str, splash_url: str) -> dict:
        """マップ画像をキャッシュ（アイコンとスプラッシュ）"""
        result = {}
        
        # Display icon
        icon_filename = f"{map_uuid}_icon.png"
        icon_filepath = self.maps_dir / icon_filename
        if icon_filepath.exists():
            result['displayIcon'] = f"/static/images/maps/{icon_filename}"
        else:
            success = await self.download_image(display_icon_url, icon_filepath)
            if success:
                result['displayIcon'] = f"/static/images/maps/{icon_filename}"
        
        # Splash image
        splash_filename = f"{map_uuid}_splash.png"
        splash_filepath = self.maps_dir / splash_filename
        if splash_filepath.exists():
            result['splash'] = f"/static/images/maps/{splash_filename}"
        else:
            success = await self.download_image(splash_url, splash_filepath)
            if success:
                result['splash'] = f"/static/images/maps/{splash_filename}"
        
        return result
    
    def get_cached_agent_image(self, agent_uuid: str) -> Optional[str]:
        """キャッシュされたエージェント画像のパスを取得"""
        filename = f"{agent_uuid}.png"
        filepath = self.agents_dir / filename
        if filepath.exists():
            return f"/static/images/agents/{filename}"
        return None
    
    def get_cached_map_images(self, map_uuid: str) -> dict:
        """キャッシュされたマップ画像のパスを取得"""
        result = {}
        
        icon_filename = f"{map_uuid}_icon.png"
        icon_filepath = self.maps_dir / icon_filename
        if icon_filepath.exists():
            result['displayIcon'] = f"/static/images/maps/{icon_filename}"
        
        splash_filename = f"{map_uuid}_splash.png"
        splash_filepath = self.maps_dir / splash_filename
        if splash_filepath.exists():
            result['splash'] = f"/static/images/maps/{splash_filename}"
        
        return result

# シングルトンインスタンス
image_cache_service = ImageCacheService()