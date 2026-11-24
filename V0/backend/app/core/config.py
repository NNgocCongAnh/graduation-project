import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Detective Case Game"
    
    # Kết nối CSDL Postgres (Mặc định dùng SQLite cho môi trường dev local nếu chưa khởi tạo Postgres)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./detective.db"
    )
    
    # Cấu hình AI Gateway qua 9Router (Local Proxy tại cổng 20128)
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "http://host.docker.internal:20128/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    
    # Model chỉ định theo yêu cầu: Nemotron-3-Super 120B Free qua 9Router Gateway
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openrouter/nvidia/nemotron-3-super-120b-a12b:free")
    LLM_TEMPERATURE: float = 0.0  # Định tính nhiệt độ = 0 để kết quả ổn định
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
