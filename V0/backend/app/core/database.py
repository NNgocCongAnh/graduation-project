from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Xử lý tham số connect_args dành riêng cho SQLite nếu đang chạy SQLite local
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Khởi tạo SQLAlchemy 2.0 Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Bật True nếu muốn log toàn bộ truy vấn SQL
    future=True
)

# Khởi tạo Factory SessionLocal
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Declarative Base Model cho các bảng CSDL
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency: Cấp phát SQLAlchemy Session cho từng request
    và tự động giải phóng / đóng session sau khi request kết thúc.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
