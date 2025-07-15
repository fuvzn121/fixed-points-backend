"""画像アップロードAPI"""
import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import aiofiles
from PIL import Image
import io

from core.database import get_db
from core.security import get_current_user
from core.config import settings
from models.user import User

router = APIRouter(prefix="/api/upload", tags=["upload"])

# 許可される画像拡張子
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = "uploads"

# アップロードディレクトリの作成
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_image(file: UploadFile) -> None:
    """画像ファイルのバリデーション"""
    # ファイル拡張子チェック
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Content-Typeチェック
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )


async def save_upload_file(upload_file: UploadFile, destination: str) -> None:
    """アップロードファイルを保存"""
    async with aiofiles.open(destination, 'wb') as out_file:
        content = await upload_file.read()
        
        # ファイルサイズチェック
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        
        # 画像として開けるかチェック
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )
        
        await out_file.write(content)


@router.post("/image", response_model=dict)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """画像をアップロード"""
    # バリデーション
    validate_image(file)
    
    # ユニークなファイル名を生成
    file_ext = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # ファイルを保存
    try:
        await save_upload_file(file, file_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save file"
        )
    
    # URLを返す
    image_url = f"/api/upload/images/{unique_filename}"
    
    return {
        "url": image_url,
        "filename": unique_filename
    }


@router.get("/images/{filename}")
async def get_image(filename: str):
    """アップロードされた画像を取得"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # 安全性のため、ファイル名を検証
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
    
    return FileResponse(file_path)


@router.post("/images/batch", response_model=List[dict])
async def upload_images_batch(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """複数の画像を一括アップロード"""
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 images allowed at once"
        )
    
    results = []
    
    for file in files:
        try:
            # バリデーション
            validate_image(file)
            
            # ユニークなファイル名を生成
            file_ext = os.path.splitext(file.filename)[1].lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # ファイルを保存
            await save_upload_file(file, file_path)
            
            # URLを追加
            image_url = f"/api/upload/images/{unique_filename}"
            results.append({
                "url": image_url,
                "filename": unique_filename
            })
        except HTTPException as e:
            # 一つでも失敗したら全体をロールバック
            for result in results:
                try:
                    os.remove(os.path.join(UPLOAD_DIR, result["filename"]))
                except:
                    pass
            raise e
    
    return results