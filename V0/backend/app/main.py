import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.api.case_router import router as case_router

# Cấu hình Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Tự động khởi tạo các bảng CSDL SQLAlchemy 2.0 trên Startup
Base.metadata.create_all(bind=engine)
logger.info("Database tables verified / created successfully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Hệ thống backend tự động sinh hồ sơ vụ án trinh thám giải đố bằng LLM qua 9Router Gateway Proxy",
    version="1.0.0"
)

# Cấu hình CORS Middleware cho phép Web Frontend React kết nối
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hỗ trợ dev local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tích hợp Router
app.include_router(case_router)

@app.get("/")
def root_status():
    return {
        "status": "online",
        "app_name": settings.PROJECT_NAME,
        "llm_gateway": settings.LLM_API_BASE,
        "model": settings.LLM_MODEL,
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
