from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from api import valorant, auth, fixed_points, upload

app = FastAPI(
    title="Fixed Points Backend",
    description="Backend API for Fixed Points application",
    version="0.1.0",
)

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],  # 複数のポートを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Fixed Points Backend is running!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 静的ファイルの配信設定
app.mount("/static", StaticFiles(directory="static"), name="static")

# APIルーターを登録
app.include_router(auth.router)
app.include_router(valorant.router)
app.include_router(fixed_points.router)
app.include_router(upload.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)