"""FastAPI Main Application and REST API Endpoints for AI Detective Game.

Provides:
- GET  /api/case/sample   -> Returns verified sample seed case.
- POST /api/case/generate -> Generates a new case using 4-step LLM pipeline & validator.
- POST /api/case/verify   -> Evaluates player deduction & crucial clues.
- GET  /api/health        -> Health check and configuration status.
"""

import os
import json
import logging
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, Query, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from models import CaseDossier, ClientCaseDossier, VerifyRequest, VerifyResponse
from llm_service import CaseGeneratorService
from validator import validate_case_logic, validate_case_diagnostics, evaluate_player_deduction
from asset_service import asset_service, STATIC_DIR
from rooms import RoomManager
from lan_discovery import start_lan_discovery, stop_lan_discovery
from database import (
    init_db,
    save_case_to_db,
    get_case_from_db,
    list_cases_from_db,
    count_cases_in_db,
    log_deduction_to_db,
    get_case_statistics
)
from security import ClientIntegrityMiddleware


# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("detective-api")

# Persistent Cases Storage Directory (JSON files)
CASES_DIR = os.path.join(os.path.dirname(__file__), "cases")
os.makedirs(CASES_DIR, exist_ok=True)

# In-memory case cache (for active game sessions)
CASE_CACHE: Dict[str, CaseDossier] = {}

def save_case_to_disk(case: CaseDossier) -> str:
    """Save case dossier to persistent JSON file in cases/."""
    file_path = os.path.join(CASES_DIR, f"{case.case_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(case.model_dump_json(indent=2))
    logger.info(f"Persisted case '{case.case_id}' to {file_path}")
    return file_path

def load_case_from_disk(case_id: str) -> Optional[CaseDossier]:
    """Load case dossier from persistent JSON file."""
    file_path = os.path.join(CASES_DIR, f"{case_id}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return CaseDossier.model_validate(data)
        except Exception as e:
            logger.error(f"Failed to read case file {file_path}: {e}")
    return None

def save_case_persistent(
    case: CaseDossier,
    is_valid: Optional[bool] = None,
    validator_score: Optional[float] = None,
    country: Optional[str] = None,
    era: Optional[str] = None,
    mystery_type: Optional[str] = None
) -> None:
    """Persist case dossier across SQLite database, disk JSON backup, and in-memory cache.

    Derives is_valid and validator_score from case.metadata telemetry if not explicitly given.
    """
    if is_valid is None:
        if case.metadata and hasattr(case.metadata, "validator_score"):
            validator_score = case.metadata.validator_score
            is_valid = (validator_score >= 1.0)
        else:
            is_valid = True
            validator_score = 1.0
    elif validator_score is None:
        validator_score = 1.0 if is_valid else 0.5

    CASE_CACHE[case.case_id] = case
    try:
        save_case_to_db(
            case,
            is_valid=is_valid,
            validator_score=validator_score,
            country=country,
            era=era,
            mystery_type=mystery_type
        )
    except Exception as e:
        logger.error(f"Failed to save case '{case.case_id}' to SQLite DB: {e}")
    try:
        save_case_to_disk(case)
    except Exception as e:
        logger.error(f"Failed to save case '{case.case_id}' to disk JSON: {e}")

def load_case_persistent(case_id: str) -> Optional[CaseDossier]:
    """Retrieve case dossier prioritizing Cache -> SQLite Database -> JSON Flat-file fallback."""
    if case_id in CASE_CACHE:
        return CASE_CACHE[case_id]
    
    # 1. Query SQLite Database
    case = get_case_from_db(case_id)
    if not case:
        # 2. Fallback to Disk JSON
        case = load_case_from_disk(case_id)
        if case:
            try:
                save_case_to_db(case)
            except Exception:
                pass
                
    if case:
        CASE_CACHE[case_id] = case
    return case

app = FastAPI(
    title="AI Detective Game Engine API",
    description="Backend service for AI-powered Detective Puzzle Game with Sequential LLM Generation & Logic Validator",
    version="1.0.0"
)

# Configure CORS: Allow explicit origins or development wildcard without credentials conflict
RAW_CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").strip()
if RAW_CORS_ORIGINS:
    cors_origins = [o.strip() for o in RAW_CORS_ORIGINS.split(",") if o.strip()]
    cors_allow_credentials = True
else:
    cors_origins = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ]
    if os.getenv("ALLOW_ALL_ORIGINS", "true").lower() in ("true", "1", "yes"):
        cors_origins = ["*"]
        cors_allow_credentials = False
    else:
        cors_allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enforce Game Client Integrity & HMAC-SHA256 Anti-Tamper Security
app.add_middleware(ClientIntegrityMiddleware)

# Mount Static Files Directory for Curated & Cached Case Assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Services
case_generator = CaseGeneratorService()

# Pre-populate sample case into SQLite DB, cache, and disk with enriched asset URLs
init_db()
sample_case = CaseGeneratorService.get_sample_case()
asset_service.enrich_case_dossier(sample_case)
save_case_persistent(sample_case)



# Preset Configurations for Realistic Procedural Settings
PRESET_SETTINGS = {
    "countries": {
        "Việt Nam": {
            "locations": [
                "Biệt thự cổ phong cách Pháp trên đồi thông Đà Lạt giữa đêm sương mù mưa bão cô lập",
                "Căn biệt thự Pháp cổ thời thuộc địa tại phố Phan Đình Phùng, Hà Nội",
                "Căn hộ Penthouse cao cấp tầng 38 khu Thảo Điền, TP. Hồ Chí Minh",
                "Nhà vườn cổ kính ven sông Thu Bồn, Hội An trong đêm mưa rằm",
                "Khu nghỉ dưỡng (Resort) biệt lập ven biển Phú Quốc giữa cơn giông biển Tây Nam"
            ],
            "eras": ["Hiện đại (2020s - Camera, thẻ từ, smartphone)", "Thập niên 1990 (Thời analog, băng cassette)", "Đông Dương (1930s - Biệt thự Pháp cổ)"]
        },
        "Nhật Bản": {
            "locations": [
                "Quán trọ truyền thống Ryokan có suối nước nóng Onsen biệt lập giữa vùng núi tuyết Nagano",
                "Biệt phủ cổ kính ngoại ô cố đô Kyoto giữa mùa lá đỏ",
                "Căn hộ cao cấp khu Ginza, Tokyo trong đêm mưa bão đô thị"
            ],
            "eras": ["Hiện đại (2020s)", "Thời kỳ Chiêu Hòa (Showa era - Thập niên 1980)"]
        },
        "Anh Quốc": {
            "locations": [
                "Trang viên cổ Blackwood giữa vùng đồng hoang Yorkshire sương mù",
                "Tòa lâu đài cổ ven hồ Loch Ness, Scotland bị cô lập do lở đá",
                "Căn hộ chung cư kiểu Victoria tại đường Baker, London"
            ],
            "eras": ["Thời đại Victoria (Cuối thế kỷ 19)", "Thập niên 1950 (Sau Thế chiến 2)", "Hiện đại (2020s)"]
        }
    },
    "mystery_types": [
        "Án mạng phòng kín (Locked-Room Mystery)",
        "Biệt thự cô lập giữa đêm mưa bão / lở đường (Isolated Manor)",
        "Tranh chấp tài sản gia tộc thượng lưu (Family Inheritance Feud)",
        "Án mạng thương trường & gián điệp công nghệ cao (Corporate Murder)"
    ]
}


class GenerateCaseRequest(BaseModel):
    """Payload to customize case generation without typing free text."""
    country: Optional[str] = Field(
        default="Việt Nam",
        description="Quốc gia bối cảnh: 'Việt Nam' (mặc định), 'Nhật Bản', 'Anh Quốc', hoặc 'Ngẫu nhiên'."
    )
    era: Optional[str] = Field(
        default="Hiện đại (2020s)",
        description="Thời kỳ lịch sử: 'Hiện đại (2020s)', 'Thập niên 1990', v.v."
    )
    setting_type: Optional[str] = Field(
        default=None,
        description="Địa điểm cụ thể hoặc để trống để hệ thống tự chọn ngẫu nhiên phù hợp thực tế."
    )
    mystery_type: Optional[str] = Field(
        default="Án mạng phòng kín (Locked-Room Mystery)",
        description="Thể loại bí ẩn trinh thám."
    )
    theme: Optional[str] = Field(
        default=None,
        description="Chủ đề tự do (tùy chọn - nếu để trống hoặc để 'string' hệ thống sẽ tự động ghép từ Quốc gia, Thời kỳ và Địa điểm)."
    )
    model: Optional[str] = Field(
        default=None,
        description="Mã mô hình LLM chỉ định (ví dụ: 'meta-llama/llama-3.3-70b-instruct:free', 'google/gemini-2.0-flash-exp:free', 'gh/gpt-4o-mini')."
    )
    api_base: Optional[str] = Field(
        default=None,
        description="Endpoint Gateway LLM (ví dụ: 'https://openrouter.ai/api/v1' hoặc 'http://localhost:20128/v1')."
    )
    api_key: Optional[str] = Field(
        default=None,
        description="Khóa xác thực API tương ứng."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "country": "Việt Nam",
                "era": "Hiện đại (2020s)",
                "setting_type": "",
                "mystery_type": "Án mạng phòng kín (Locked-Room Mystery)",
                "theme": "",
                "model": "meta-llama/llama-3.3-70b-instruct:free"
            }
        }
    }


# Danh mục các mô hình AI phục vụ Game & Nghiên cứu (Ưu tiên mô hình Free hàng ngày)
AVAILABLE_MODELS = [
    {
        "id": "gemini/gemma-4-31b-it",
        "name": "Gemma 4 31B Instruct (Gemini Provider)",
        "category": "free",
        "provider": "Google Gemini / 9Router",
        "is_free": True,
        "recommended": True,
        "badge": "⭐ MẶC ĐỊNH",
        "description": "Mô hình Gemma 4 31B chạy qua nhà cung cấp Gemini (hỗ trợ gắn API Key nâng cấp qua 9Router)."
    },
    {
        "id": "gemma4:e4b-it-qat",
        "name": "Gemma 4 E4B Local (Offline Ollama)",
        "category": "local",
        "provider": "Local Ollama (RTX 3050)",
        "is_free": True,
        "recommended": True,
        "badge": "💻 OFFLINE",
        "description": "Mô hình Gemma 4 cỡ nhỏ chạy cục bộ hoàn toàn miễn phí và không cần Internet (dùng làm fallback cuối)."
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B Instruct (Free)",
        "category": "free",
        "provider": "OpenRouter",
        "is_free": True,
        "recommended": True,
        "badge": "⭐ KHUYÊN DÙNG",
        "description": "Mô hình mã nguồn mở 70B mạnh nhất hiện nay, hoàn toàn miễn phí hàng ngày, suy luận tiếng Việt xuất sắc."
    },
    {
        "id": "google/gemini-2.0-flash-exp:free",
        "name": "Gemini 2.0 Flash (Free)",
        "category": "free",
        "provider": "OpenRouter / Google",
        "is_free": True,
        "recommended": True,
        "badge": "⚡ SIÊU TỐC",
        "description": "Thế hệ mới nhất từ Google DeepMind, phản hồi cực nhanh dưới 5s, miễn phí hàng ngày."
    },
    {
        "id": "google/gemini-2.0-flash-thinking-exp:free",
        "name": "Gemini 2.0 Flash Thinking (Free)",
        "category": "free",
        "provider": "OpenRouter / Google",
        "is_free": True,
        "recommended": True,
        "badge": "🧠 SUY LUẬN SÂU",
        "description": "Mô hình suy luận chuỗi tư duy (Chain-of-Thought) độc quyền, phân tích logic vụ án rất chặt chẽ."
    },
    {
        "id": "deepseek/deepseek-r1:free",
        "name": "DeepSeek R1 Reasoning (Free)",
        "category": "free",
        "provider": "OpenRouter / DeepSeek",
        "is_free": True,
        "recommended": True,
        "badge": "🎯 TOÁN & LOGIC",
        "description": "Mô hình suy luận tương đương OpenAI o1, tư duy logic y pháp cực mạnh, miễn phí hàng ngày."
    },
    {
        "id": "deepseek/deepseek-chat:free",
        "name": "DeepSeek V3 Chat (Free)",
        "category": "free",
        "provider": "OpenRouter / DeepSeek",
        "is_free": True,
        "recommended": False,
        "badge": "FREE",
        "description": "Mô hình MoE 671B tham số đỉnh cao, văn phong tiếng Việt rất tự nhiên."
    },
    {
        "id": "qwen/qwen-2.5-72b-instruct:free",
        "name": "Qwen 2.5 72B Instruct (Free)",
        "category": "free",
        "provider": "OpenRouter / Alibaba",
        "is_free": True,
        "recommended": False,
        "badge": "FREE",
        "description": "Mô hình 72B từ Alibaba, tuân thủ Pydantic Schema JSON cực kỳ chuẩn xác."
    },
    {
        "id": "nvidia/nemotron-3-super-120b-a12b:free",
        "name": "NVIDIA Nemotron 3 120B (Free)",
        "category": "free",
        "provider": "OpenRouter / NVIDIA",
        "is_free": True,
        "recommended": False,
        "badge": "FREE",
        "description": "Mô hình siêu tham số của NVIDIA, phân tích bối cảnh rất chi tiết."
    },
    {
        "id": "gh/gpt-4o-mini",
        "name": "GPT-4o-Mini (Research Benchmark)",
        "category": "research",
        "provider": "GitHub Models / OpenAI",
        "is_free": False,
        "recommended": True,
        "badge": "🎓 BÀI BÁO",
        "description": "Mô hình đo đạc trong Luận văn Tốt nghiệp: Schema Valid 100%, Logic Pass 100%, P50 10.88s."
    },
    {
        "id": "gh/gpt-4o",
        "name": "GPT-4o Flagship (Research Benchmark)",
        "category": "research",
        "provider": "GitHub Models / OpenAI",
        "is_free": False,
        "recommended": False,
        "badge": "🎓 BÀI BÁO",
        "description": "Mô hình cờ đầu trong Luận văn: SOTA Reasoning, P50 19.53s, ca nghiên cứu Lượt 5."
    },
    {
        "id": "ollama/gemma4:31b-cloud",
        "name": "Gemma 4 31B Cloud (Research Benchmark)",
        "category": "research",
        "provider": "Ollama / Open-Weights",
        "is_free": True,
        "recommended": True,
        "badge": "🎓 BÀI BÁO",
        "description": "Mô hình đối sánh mã nguồn mở trong Luận văn: P50 10.73s, Logic Pass 100%."
    }
]


class UpdateSettingsRequest(BaseModel):
    """Payload to update LLM configuration at runtime."""
    model: Optional[str] = Field(default=None, description="Mã mô hình LLM mong muốn")
    api_base: Optional[str] = Field(default=None, description="Endpoint API Gateway")
    api_key: Optional[str] = Field(default=None, description="API Key")


def _clean_field(val: Optional[str]) -> Optional[str]:
    """Helper to clean dummy Swagger UI values like 'string', 'null', 'none'."""
    if not val:
        return None
    cleaned = val.strip()
    if cleaned.lower() in ("string", "null", "none", ""):
        return None
    return cleaned


@app.get("/")
def root():
    """Root status endpoint."""
    return {
        "status": "online",
        "service": "AI Detective Game Engine API",
        "endpoints": {
            "sample_case": "/api/case/sample",
            "generate_case": "/api/case/generate",
            "verify_solution": "/api/case/verify",
            "docs": "/docs"
        }
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "cached_cases_count": len(CASE_CACHE),
        "llm_model": case_generator.model,
        "llm_gateway": case_generator.api_base
    }


@app.get("/api/case/sample", response_model=ClientCaseDossier)
def get_sample_case():
    """Retrieve verified sample seed case dossier for offline testing and initial game load.

    Returns sanitized ClientCaseDossier without secret ground truth or cheat flags.
    """
    case = CaseGeneratorService.get_sample_case()
    asset_service.enrich_case_dossier(case)
    CASE_CACHE[case.case_id] = case
    return case.to_client_dossier()


@app.get("/api/case/all")
def list_all_cases():
    """List all saved cases currently in SQLite database and disk storage."""
    db_cases = list_cases_from_db(limit=None)
    if db_cases:
        return {"total_cases": len(db_cases), "cases": db_cases}

    cases = []
    # Fallback to disk storage
    if os.path.exists(CASES_DIR):
        for filename in os.listdir(CASES_DIR):
            if filename.endswith(".json"):
                cid = filename.replace(".json", "")
                c = load_case_persistent(cid)
                if c:
                    cases.append({
                        "case_id": c.case_id,
                        "title": c.title,
                        "summary": c.summary,
                        "culprit_id": c.ground_truth.culprit_id,
                        "suspects_count": len(c.suspects),
                        "evidences_count": len(c.evidences)
                    })
    return {"total_cases": len(cases), "cases": cases}


@app.get("/api/cases")
def query_cases(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items per page"),
    country: Optional[str] = Query(None, description="Filter by setting country"),
    mystery_type: Optional[str] = Query(None, description="Filter by mystery genre"),
    is_valid_only: bool = Query(False, description="Filter only logically verified cases")
):
    """Query case catalog with pagination and criteria filtering for game lobby and research."""
    filters = {"country": country, "mystery_type": mystery_type, "is_valid_only": is_valid_only}
    records = list_cases_from_db(skip=skip, limit=limit, **filters)
    total = count_cases_in_db(**filters)
    return {"total": total, "skip": skip, "limit": limit, "items": records}


@app.get("/api/case/presets")
def get_case_presets():
    """Retrieve available realistic presets (countries, locations, eras, mystery types) for UI dropdowns."""
    return PRESET_SETTINGS


@app.get("/api/case/{case_id}", response_model=ClientCaseDossier)
def get_case_by_id(case_id: str):
    """Retrieve a specific case dossier by its ID from memory, SQLite DB, or disk.

    Returns sanitized ClientCaseDossier for client gameplay without spoiler flags.
    """
    case = load_case_persistent(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    asset_service.enrich_case_dossier(case)
    return case.to_client_dossier()


@app.get("/api/case/{case_id}/internal", response_model=CaseDossier)
def get_internal_case_by_id(case_id: str):
    """Retrieve full internal case dossier with Ground Truth for benchmark runners and evaluation."""
    case = load_case_persistent(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    asset_service.enrich_case_dossier(case)
    return case


@app.get("/api/case/{case_id}/graph")
def get_case_bipartite_graph(case_id: str):
    """Retrieve explicit Bipartite Graph representation (nodes & edges) for Corkboard visualization."""
    from case_graph import build_bipartite_case_graph
    case = load_case_persistent(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    return build_bipartite_case_graph(case)


@app.get("/api/case/{case_id}/stats")
def get_case_stats(case_id: str):
    """Retrieve player deduction analytics and difficulty statistics for a given case."""
    case = load_case_persistent(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    return get_case_statistics(case_id)


@app.get("/api/settings/models")
def get_available_models():
    """Retrieve catalog of AI models: OpenRouter free models and research benchmark models."""
    return {
        "active_model": case_generator.model,
        "active_api_base": case_generator.api_base,
        "models": AVAILABLE_MODELS
    }


@app.get("/api/settings")
def get_current_settings():
    """Get active LLM runtime configuration."""
    key = case_generator.api_key or ""
    masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
    return {
        "model": case_generator.model,
        "api_base": case_generator.api_base,
        "api_key_masked": masked_key,
        "available_models_count": len(AVAILABLE_MODELS)
    }


@app.post("/api/settings")
def update_settings(payload: UpdateSettingsRequest):
    """Dynamically switch active LLM model or API credentials at runtime."""
    new_model = _clean_field(payload.model)
    new_base = _clean_field(payload.api_base)
    new_key = _clean_field(payload.api_key)

    case_generator.update_config(model=new_model, api_base=new_base, api_key=new_key)
    logger.info(f"Updated backend AI settings: model={case_generator.model}")
    return {
        "status": "success",
        "message": f"Cấu hình mô hình AI đã được cập nhật thành '{case_generator.model}'",
        "model": case_generator.model,
        "api_base": case_generator.api_base
    }


@app.post("/api/case/generate", response_model=ClientCaseDossier)
async def generate_case(payload: GenerateCaseRequest = Body(default_factory=GenerateCaseRequest)):
    """Generate a new logically verified Case Dossier via 4-step LLM pipeline and save to disk."""
    import random
    try:
        # Sanitize dummy Swagger UI default values ("string", "null", "")
        raw_theme = _clean_field(payload.theme)
        country = _clean_field(payload.country) or "Việt Nam"
        location = _clean_field(payload.setting_type)
        era = _clean_field(payload.era)
        mystery = _clean_field(payload.mystery_type)

        # Handle per-request model override
        req_model = _clean_field(payload.model)
        req_base = _clean_field(payload.api_base)
        req_key = _clean_field(payload.api_key)

        if req_model or req_base or req_key:
            active_gen = CaseGeneratorService(
                api_base=req_base or case_generator.api_base,
                api_key=req_key or case_generator.api_key,
                model=req_model or case_generator.model
            )
        else:
            active_gen = case_generator

        # If no custom free-text theme provided, automatically synthesize from realistic country/era/location presets
        if not raw_theme:
            if country == "Ngẫu nhiên" or country not in PRESET_SETTINGS["countries"]:
                country = random.choice(list(PRESET_SETTINGS["countries"].keys()))
            
            country_data = PRESET_SETTINGS["countries"].get(country, PRESET_SETTINGS["countries"]["Việt Nam"])
            location = location or random.choice(country_data["locations"])
            era = era or random.choice(country_data["eras"])
            mystery = mystery or random.choice(PRESET_SETTINGS["mystery_types"])
            
            theme = (
                f"{mystery} tại {country}. "
                f"Bối cảnh cụ thể: {location}. Thời kỳ: {era}. "
                f"YÊU CẦU BẮT BUỘC: Toàn bộ nhân vật (nạn nhân, nghi phạm, nhân chứng) "
                f"phải có họ tên thuần người {country} chân thực (ví dụ Việt Nam: Nguyễn, Trần, Lê, Vũ, Hoàng, Phạm,...). "
                f"Bối cảnh và nghề nghiệp phải hoàn toàn sát với đời sống thực tế tại {country}."
            )
        else:
            theme = raw_theme
            if country and country != "Ngẫu nhiên" and country.lower() not in theme.lower():
                theme += f" (Bối cảnh: {country}, thời kỳ: {era or 'Hiện đại'}, nhân vật mang tên người {country})"

        logger.info(f"Generating case with synthesized theme: '{theme}' (Model: {active_gen.model})")
        case = await active_gen.generate_case(theme=theme)

        # Rigorous Neuro-Symbolic Validation Check
        diag = validate_case_diagnostics(case)
        is_valid = diag.is_valid
        validator_score = 1.0 if is_valid else 0.5
        if case.metadata:
            case.metadata.validator_score = validator_score

        # Block invalid cases fail-closed with HTTP 422
        if not is_valid:
            save_case_persistent(case, is_valid=False, validator_score=validator_score, country=country, era=era, mystery_type=mystery)
            logger.warning(f"Case '{case.case_id}' failed neuro-symbolic validation ({len(diag.violations)} violations). Blocking with HTTP 422.")
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Case failed neuro-symbolic validation after localized repair retries.",
                    "case_id": case.case_id,
                    "is_valid": False,
                    "validator_score": validator_score,
                    "violations": [v.model_dump() for v in diag.violations],
                    "message": "Hồ sơ vụ án không đáp ứng tiêu chuẩn tính giải được hoặc vi phạm tính nhất quán logic."
                }
            )

        # Enrich valid case with semantic assets
        asset_service.enrich_case_dossier(case)
        # Save to memory cache, SQLite database, and persistent disk storage
        save_case_persistent(case, is_valid=True, validator_score=1.0, country=country, era=era, mystery_type=mystery)
        return case.to_client_dossier()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate case: {e}")
        raise HTTPException(status_code=500, detail=f"Case generation error: {str(e)}")


@app.post("/api/case/verify", response_model=VerifyResponse)
def verify_solution(request: VerifyRequest):
    """Verify player's deduction using Neuro-Symbolic scoring (fair-play constraints) and persist audit log."""
    case = load_case_persistent(request.case_id)
    if not case:
        # Fallback to checking sample case if ID matches
        if request.case_id == sample_case.case_id:
            case = sample_case
        else:
            raise HTTPException(status_code=404, detail=f"Case ID '{request.case_id}' not found in active session or database.")

    response = evaluate_player_deduction(
        case=case,
        accused_id=request.selected_suspect_id,
        selected_clue_ids=request.selected_evidence_ids,
        reasoning=request.reasoning
    )

    # Persist deduction trial to database audit log for research analytics
    try:
        log_deduction_to_db(
            case_id=request.case_id,
            verify_req=request,
            verify_res=response
        )
    except Exception as e:
        logger.warning(f"Could not log deduction to DB: {e}")

    return response


# ---------------------------------------------------------
# Realtime Multiplayer Room & Corkboard Sync WebSockets
# ---------------------------------------------------------

room_manager = RoomManager()


@app.on_event("startup")
async def _start_lan_discovery():
    await start_lan_discovery(http_port=int(os.getenv("PORT", "8000")))


@app.on_event("shutdown")
async def _stop_lan_discovery():
    stop_lan_discovery()


@app.get("/api/rooms/{room_id}")
def get_room_info(room_id: str):
    """Lobby info: who is in the room and whether there is a free seat."""
    room = room_manager.get_room(room_id)
    players = room.player_names if room else []
    return {
        "room_id": room_id,
        "players": players,
        "max_players": room_manager.max_players,
        "is_full": len(players) >= room_manager.max_players,
        "case_id": room.case_id if room else None
    }


@app.websocket("/ws/rooms/{room_id}")
async def websocket_room_endpoint(websocket: WebSocket, room_id: str, name: Optional[str] = Query(None)):
    """Co-op endpoint (max 3 players): board sync, chat, presence and push-to-talk voice."""
    player = await room_manager.join(room_id, websocket, name)
    if player is None:
        return
    try:
        while True:
            frame = await websocket.receive()
            if frame["type"] == "websocket.disconnect":
                break
            if frame.get("bytes") is not None:
                await room_manager.relay_audio(room_id, websocket, frame["bytes"])
            elif frame.get("text"):
                try:
                    data = json.loads(frame["text"])
                except json.JSONDecodeError:
                    continue
                await room_manager.handle_message(room_id, websocket, data)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error in room '{room_id}': {e}")
    finally:
        await room_manager.leave(room_id, websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
