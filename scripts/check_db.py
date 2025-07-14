"""データベースのテーブル確認スクリプト"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import inspect
from core.database import engine

def check_tables():
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("📊 データベース内のテーブル一覧:")
    print("-" * 40)
    for table in tables:
        columns = inspector.get_columns(table)
        print(f"\n✅ {table}")
        for col in columns:
            print(f"   - {col['name']} ({col['type']})")
    
    print(f"\n合計: {len(tables)} テーブル")

if __name__ == "__main__":
    check_tables()