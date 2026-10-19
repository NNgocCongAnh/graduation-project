"""Asset Service for AI Detective Game Engine.

Implements the Hybrid Semantic Asset Architecture:
1. Curated Asset Bank: Instant, distortion-free archetype images (0.01s latency).
2. Semantic Rule & Tag Matching: Maps LLM-generated suspects and clues to optimal assets.
3. On-Demand Cloudflare Workers AI / Local Generator: For bespoke items, with automated disk caching.
"""

import os
import re
import hashlib
import logging
from typing import Optional, List, Dict, Tuple
from urllib.parse import urljoin

logger = logging.getLogger("detective-assets")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ASSETS_DIR = os.path.join(STATIC_DIR, "assets")
SUSPECTS_DIR = os.path.join(ASSETS_DIR, "suspects")
EVIDENCES_DIR = os.path.join(ASSETS_DIR, "evidences")
CACHE_DIR = os.path.join(STATIC_DIR, "cache")

os.makedirs(SUSPECTS_DIR, exist_ok=True)
os.makedirs(EVIDENCES_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# Cloudflare Workers AI Environment Variables
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

# Semantic Keyword Dictionaries for Suspect Archetypes
SUSPECT_ARCHETYPE_RULES: List[Dict] = [
    {
        "filename": "butler_male_50s.png",
        "keywords": ["quản gia", "butler", "gia nhân", "người hầu", "valet", "steward", "phục vụ"],
        "gender": "male",
        "min_age": 40,
        "max_age": 75
    },
    {
        "filename": "businessman_male_50s.png",
        "keywords": ["doanh nhân", "businessman", "bác sĩ", "doctor", "luật sư", "lawyer", "chủ", "giám đốc", "triệu phú", "nhà sưu tầm", "collector", "ông trùm", "chủ tịch"],
        "gender": "male",
        "min_age": 35,
        "max_age": 75
    },
    {
        "filename": "female_30s.png",
        "keywords": ["tiểu thư", "cháu gái", "con gái", "nghệ sĩ", "nhiếp ảnh", "bà", "cô", "phu nhân", "heiress", "lady", "nữ bác sĩ", "nữ"],
        "gender": "female",
        "min_age": 18,
        "max_age": 60
    },
    {
        "filename": "young_male_20s.png",
        "keywords": ["cháu trai", "con trai", "nghệ sĩ", "nhiếp ảnh", "nhạc sĩ", "sinh viên", "thanh niên", "cậu", "anh", "young", "artist", "son"],
        "gender": "male",
        "min_age": 18,
        "max_age": 35
    }
]

# Semantic Keyword Dictionaries for Evidence Archetypes
EVIDENCE_ARCHETYPE_RULES: List[Dict] = [
    {
        "filename": "pocket_watch_broken.png",
        "keywords": ["đồng hồ", "watch", "clock", "thời gian", "kim đồng hồ", "bỏ túi", "timepiece", "mặt kính vỡ"]
    },
    {
        "filename": "evidence_glass.png",
        "keywords": ["dao", "knife", "dagger", "hung khí", "kính", "mặt kính", "thủy tinh", "mảnh vỡ", "kính mắt", "cửa sổ", "glass", "lens", "spectacles"]
    },
    {
        "filename": "evidence_teacup.png",
        "keywords": ["tách", "chén", "cốc", "trà", "cà phê", "ly", "uống", "cup", "teacup", "coffee", "bình trà", "chất độc", "an thần", "thuốc"]
    }
]


class AssetService:
    """Manages asset matching, on-demand generation, and static URLs."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url.rstrip("/")

    def _infer_gender(self, name: str, occupation: str, statement: str) -> str:
        """Infer gender from Vietnamese/English naming and pronouns."""
        text = f"{name} {occupation} {statement}".lower()
        female_clues = ["nữ", "bà", "cô", "chị", "tiểu thư", "eleanor", "emma", "sarah", "mary", "mrs", "ms", "lady"]
        male_clues = ["nam", "ông", "anh", "cậu", "william", "arthur", "julian", "john", "mr", "lord", "sir"]

        score_f = sum(1 for w in female_clues if re.search(r"\b" + re.escape(w) + r"\b", text))
        score_m = sum(1 for w in male_clues if re.search(r"\b" + re.escape(w) + r"\b", text))

        return "female" if score_f > score_m else "male"

    def match_suspect_asset(self, name: str, age: int, occupation: str, alibi_statement: str = "") -> str:
        """Match suspect details to the best available curated portrait."""
        inferred_gender = self._infer_gender(name, occupation, alibi_statement)
        text_corpus = f"{name} {occupation} {alibi_statement}".lower()

        best_match = None
        highest_score = -999

        for rule in SUSPECT_ARCHETYPE_RULES:
            score = 0
            # Strict Gender match: Penalize heavily if gender differs
            if rule["gender"] == inferred_gender:
                score += 10
            else:
                score -= 20

            # Age range match
            if rule["min_age"] <= age <= rule["max_age"]:
                score += 5

            # Keyword match
            for kw in rule["keywords"]:
                if kw in text_corpus:
                    score += 4

            if score > highest_score:
                highest_score = score
                best_match = rule["filename"]

            for kw in rule["keywords"]:
                if kw in text_corpus:
                    score += 4

            if score > highest_score:
                highest_score = score
                best_match = rule["filename"]

        matched_file = best_match or "butler_male_50s.png"
        return f"{self.base_url}/static/assets/suspects/{matched_file}"

    def match_evidence_asset(self, title: str, description: str, location: str = "") -> str:
        """Match evidence details to the best available curated clue photo."""
        text_corpus = f"{title} {description} {location}".lower()

        best_match = None
        highest_score = -1

        for rule in EVIDENCE_ARCHETYPE_RULES:
            score = 0
            for kw in rule["keywords"]:
                if kw in text_corpus:
                    score += 3

            if score > highest_score:
                highest_score = score
                best_match = rule["filename"]

        matched_file = best_match or "pocket_watch_broken.png"
        return f"{self.base_url}/static/assets/evidences/{matched_file}"

    def generate_on_demand_cloudflare(self, prompt: str, cache_key: str) -> Optional[str]:
        """Optionally generate a bespoke image via Cloudflare Workers AI FLUX.1."""
        if not CF_ACCOUNT_ID or not CF_API_TOKEN:
            return None

        import urllib.request
        import json

        cache_filename = f"{hashlib.md5(cache_key.encode()).hexdigest()}.png"
        cache_path = os.path.join(CACHE_DIR, cache_filename)

        if os.path.exists(cache_path):
            return f"{self.base_url}/static/cache/{cache_filename}"

        url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = json.dumps({"prompt": prompt, "steps": 4}).encode()

        try:
            req = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                # Cloudflare returns raw image bytes or json with b64 image
                with open(cache_path, "wb") as f:
                    f.write(data)
                return f"{self.base_url}/static/cache/{cache_filename}"
        except Exception as e:
            logger.warning(f"Cloudflare Workers AI generation failed ({e}), falling back to curated assets.")
            return None

    def enrich_case_dossier(self, case_dossier) -> None:
        """Enrich all suspects and evidences in a CaseDossier with image URLs."""
        for s in case_dossier.suspects:
            s.image_url = self.match_suspect_asset(
                name=s.name,
                age=s.age,
                occupation=s.occupation,
                alibi_statement=s.alibi_statement
            )

        for ev in case_dossier.evidences:
            ev.image_url = self.match_evidence_asset(
                title=ev.title,
                description=ev.description,
                location=ev.location
            )


# Singleton Instance
asset_service = AssetService()
