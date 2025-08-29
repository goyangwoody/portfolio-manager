"""
Database dependency and configuration
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가 (api/ 디렉토리에서 상위로)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from src.pm.db.models import SessionLocal

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
