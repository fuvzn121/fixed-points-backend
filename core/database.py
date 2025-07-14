from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# データベースエンジンの作成
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"options": "-c timezone=utc"},  # PostgreSQL用のタイムゾーン設定
    pool_pre_ping=True,  # 接続の有効性を事前チェック
    pool_size=5,
    max_overflow=10
)

# セッションローカルクラスの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスの作成
Base = declarative_base()


# データベースセッションの依存性注入用
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()