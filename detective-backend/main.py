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
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from models import CaseDossier, VerifyRequest, VerifyResponse
from llm_service import CaseGeneratorService
from validator import validate_case_logic
from asset_service import asset_service, STATIC_DIR


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

app = FastAPI(
    title="AI Detective Game Engine API",
    description="Backend service for AI-powered Detective Puzzle Game with Sequential LLM Generation & Logic Validator",
    version="1.0.0"
)

# Enable CORS for Unity WebGL and Frontend Clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files Directory for Curated & Cached Case Assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Services
case_generator = CaseGeneratorService()

# Pre-populate sample case into cache and disk with enriched asset URLs
sample_case = CaseGeneratorService.get_sample_case()
asset_service.enrich_case_dossier(sample_case)
CASE_CACHE[sample_case.case_id] = sample_case
save_case_to_disk(sample_case)



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

    model_config = {
        "json_schema_extra": {
            "example": {
                "country": "Việt Nam",
                "era": "Hiện đại (2020s)",
                "setting_type": "",
                "mystery_type": "Án mạng phòng kín (Locked-Room Mystery)",
                "theme": ""
            }
        }
    }


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


@app.get("/api/case/sample", response_model=CaseDossier)
def get_sample_case():
    """Retrieve verified sample seed case dossier for offline testing and initial game load."""
    case = CaseGeneratorService.get_sample_case()
    asset_service.enrich_case_dossier(case)
    CASE_CACHE[case.case_id] = case
    return case


@app.get("/api/case/all")
def list_all_cases():
    """List all saved cases currently in memory and disk storage."""
    cases = []
    # Check disk storage
    if os.path.exists(CASES_DIR):
        for filename in os.listdir(CASES_DIR):
            if filename.endswith(".json"):
                cid = filename.replace(".json", "")
                c = CASE_CACHE.get(cid) or load_case_from_disk(cid)
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


@app.get("/api/case/presets")
def get_case_presets():
    """Retrieve available realistic presets (countries, locations, eras, mystery types) for UI dropdowns."""
    return PRESET_SETTINGS


@app.get("/api/case/{case_id}", response_model=CaseDossier)
def get_case_by_id(case_id: str):
    """Retrieve a specific case dossier by its ID from memory or persistent disk."""
    case = CASE_CACHE.get(case_id) or load_case_from_disk(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    asset_service.enrich_case_dossier(case)
    CASE_CACHE[case.case_id] = case
    return case



@app.get("/api/case/{case_id}/graph")
def get_case_bipartite_graph(case_id: str):
    """Retrieve explicit Bipartite Graph representation (nodes & edges) for Corkboard visualization."""
    from case_graph import build_bipartite_case_graph
    case = CASE_CACHE.get(case_id) or load_case_from_disk(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case with ID '{case_id}' not found.")
    return build_bipartite_case_graph(case)


@app.post("/api/case/generate", response_model=CaseDossier)
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

        logger.info(f"Generating case with synthesized theme: '{theme}'")
        case = await case_generator.generate_case(theme=theme)
        # Enrich with semantic assets
        asset_service.enrich_case_dossier(case)
        # Save to memory cache and persistent disk storage
        CASE_CACHE[case.case_id] = case
        save_case_to_disk(case)
        return case

    except Exception as e:
        logger.error(f"Failed to generate case: {e}")
        raise HTTPException(status_code=500, detail=f"Case generation error: {str(e)}")


@app.post("/api/case/verify", response_model=VerifyResponse)
def verify_solution(request: VerifyRequest):
    """Verify player's deduction (accused suspect and submitted crucial evidence IDs)."""
    case = CASE_CACHE.get(request.case_id) or load_case_from_disk(request.case_id)
    if not case:
        # Fallback to checking sample case if ID matches
        if request.case_id == sample_case.case_id:
            case = sample_case
        else:
            raise HTTPException(status_code=404, detail=f"Case ID '{request.case_id}' not found in active session or database.")

    ground_truth = case.ground_truth
    culprit_identified = (request.selected_suspect_id == ground_truth.culprit_id)

    # Calculate crucial evidence identification
    crucial_evidences = [ev for ev in case.evidences if ev.is_crucial]
    crucial_ev_ids = {ev.id for ev in crucial_evidences}
    selected_ev_ids = set(request.selected_evidence_ids)

    found_crucial = selected_ev_ids.intersection(crucial_ev_ids)
    crucial_evidences_identified = len(found_crucial) >= 1  # At least 1 decisive clue identified

    is_correct = culprit_identified and crucial_evidences_identified

    if is_correct:
        feedback = (
            f"CHÍNH XÁC! Bạn đã phá giải thành công vụ án '{case.title}'. "
            f"Hung thủ thực sự chính là {ground_truth.culprit_id}!"
        )
        contradiction = ground_truth.core_contradiction
    elif not culprit_identified:
        feedback = "LẬP LUẬN SAI! Đối tượng bạn cáo buộc không phải là hung thủ thực sự. Hãy xem xét kỹ lại Alibi và thời gian tử vong."
        contradiction = None
    else:
        feedback = "GẦN ĐÚNG! Bạn đã chỉ ra đúng hung thủ, nhưng chứng cứ bạn đưa ra chưa đủ sức thuyết phục để vạch trần mâu thuẫn!"
        contradiction = None

    return VerifyResponse(
        case_id=case.case_id,
        is_correct=is_correct,
        culprit_identified=culprit_identified,
        crucial_evidences_identified=crucial_evidences_identified,
        found_crucial_count=len(found_crucial),
        total_crucial_count=len(crucial_ev_ids),
        feedback=feedback,
        core_contradiction=contradiction
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
