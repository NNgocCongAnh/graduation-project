"""Specialized Agents for Procedural Case Generation & Localized Patch Repair.

Implements the multi-agent role decomposition from Paper 3 (arXiv:2604.11741):
1. OutlineAgent: Generates crime premise, victim forensics, and hidden Ground Truth.
2. CharacterAgent: Synthesizes suspects with distinct motives, alibis, and innocent secrets.
3. ClueAgent: Generates indirect physical traces, alibi-breaking crucial clues, and red herrings.
4. DeductionAgent (QaAgent): Synthesizes multi-hop reasoning chains connecting clues to culprit.

Each agent provides localized repair methods (Paper 7: ConWriter) to fix specific
constraint violations without discarding the entire narrative.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from openai import AsyncOpenAI
from pydantic import ValidationError

from models import (
    Victim, Suspect, Evidence, GroundTruth, ForensicData,
    ReasoningChain, DeductionStep, ConstraintViolation
)

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for specialized generative agents."""

    FALLBACK_CANDIDATES = [
        ("http://localhost:20128/v1", "sk-9router-local", "gemini/gemma-4-31b-it"),
        ("http://localhost:20128/v1", "sk-9router-local", "gh/gpt-3.5-turbo-0613"),
        ("http://localhost:20128/v1", "sk-9router-local", "gh/gpt-4o-mini"),
        ("http://localhost:11434/v1", "ollama", "gemma4:e4b-it-qat"),
    ]

    def __init__(self, client: AsyncOpenAI, model: str):
        self.client = client
        self.model = model
        self.last_used_model: str = model
        self.fallback_used: bool = False

    @staticmethod
    def _clean_json_string(text: str) -> str:
        """Strip markdown code blocks, reasoning traces, and extract outermost JSON."""
        import re
        text = text.strip()
        # Strip thinking blocks from reasoning models
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        # Strip markdown fences
        if "```" in text:
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
        # Fallback to outermost braces
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]
        return text

    async def _invoke_single_model(self, client: AsyncOpenAI, model: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Invoke a single LLM endpoint and parse non-empty JSON payload."""
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        raw_text = response.choices[0].message.content or "{}"
        clean_text = self._clean_json_string(raw_text)
        parsed = json.loads(clean_text)
        if not parsed:
            raise ValueError(f"Empty JSON object returned by model '{model}'")
        return parsed

    async def _call_llm_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call primary OpenAI-compatible LLM endpoint with per-agent smart fallback."""
        agent_name = self.__class__.__name__
        try:
            data = await self._invoke_single_model(self.client, self.model, system_prompt, user_prompt)
            self.last_used_model = self.model
            self.fallback_used = False
            return data
        except Exception as primary_err:
            logger.warning(f"[{agent_name}] Primary model '{self.model}' failed ({primary_err}). Initiating fallback chain...")

        primary_base = str(self.client.base_url).rstrip("/") if getattr(self.client, "base_url", None) else ""
        last_err: Optional[Exception] = None

        for fb_base, fb_key, fb_model in self.FALLBACK_CANDIDATES:
            if fb_model == self.model and fb_base.rstrip("/") == primary_base:
                continue
            try:
                fb_client = AsyncOpenAI(base_url=fb_base, api_key=fb_key)
                data = await self._invoke_single_model(fb_client, fb_model, system_prompt, user_prompt)
                self.last_used_model = fb_model
                self.fallback_used = True
                logger.warning(f"[{agent_name}] Fallback activated: '{self.model}' -> '{fb_model}'")
                return data
            except Exception as fb_err:
                last_err = fb_err
                logger.warning(f"[{agent_name}] Fallback model '{fb_model}' failed ({fb_err}).")

        raise RuntimeError(f"[{agent_name}] All primary and fallback models failed. Last error: {last_err}")


class OutlineAgent(BaseAgent):
    """Responsible for setting, victim forensics, and secret Ground Truth."""

    async def generate(self, theme: str) -> Tuple[str, str, Victim, GroundTruth]:
        system_prompt = (
            "You are a Master Mystery Architect (OutlineAgent). "
            "Your task is to establish a locked-room mystery outline, victim forensic data, and the absolute Ground Truth. "
            "CRITICAL CULTURAL RULE: All names (victim name, suspects), locations, and vocabulary MUST be authentic and strictly match the Country and Culture specified in the Theme (e.g. if Vietnam, victim MUST have a realistic Vietnamese name like 'Nguyễn Văn Hải', 'Trần Đình Trọng', 'Lê Hữu Đạt', etc. NEVER use English names like 'Arthur Blackwood' unless theme is in UK). "
            "Output JSON with title, summary, victim (name, age, occupation, forensic_data), and ground_truth. "
            "FORENSIC RULES: ambient_temp between 18.0 and 24.0°C; body_temp between 28.0 and 34.0°C. "
            "Also give body_weight_kg (45-120), cooling_factor (Henssge C: 1.0 clothed in still air, 0.8 lightly dressed/draughty, 1.2 under a blanket) "
            "and discovery_time (HH:MM when the body was found and rectal temperature measured, typically 8-14 hours after the murder). "
            "The time-of-death window is recomputed by a Henssge physics engine from these values, so keep them realistic. "
            "ground_truth.actual_crime_time must be roughly discovery_time minus the cooling time implied by body_temp. "
            "ground_truth.culprit_id must be 'SUSP-01'."
        )
        user_prompt = f"""
Theme: {theme}
Format:
{{
  "title": "<Tên vụ án tiếng Việt hấp dẫn phù hợp chủ đề>",
  "summary": "<Mô tả bối cảnh vụ án phòng kín 2-3 câu sát thực tế>",
  "victim": {{
    "name": "<Họ tên nạn nhân bản địa chuẩn xác>",
    "age": 55,
    "occupation": "<Nghề nghiệp phù hợp>",
    "forensic_data": {{
      "ambient_temp": 20.0,
      "body_temp": 31.5,
      "livor_mortis_state": "Hoen ố cố định ở lưng, không biến mất khi ấn",
      "wound_description": "Vết thương trí mạng ở vùng ngực trái",
      "estimated_tod_start": "20:06",
      "estimated_tod_end": "23:06",
      "body_weight_kg": 70.0,
      "cooling_factor": 1.0,
      "discovery_time": "08:30"
    }}
  }},
  "ground_truth": {{
    "culprit_id": "SUSP-01",
    "actual_crime_time": "21:40",
    "murder_weapon": "<Hung khí gây án>",
    "core_contradiction": "<Mâu thuẫn then chốt giữa lời khai của hung thủ và manh mối vật lý hiện trường>"
  }}
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        victim = Victim.model_validate(data["victim"])
        ground_truth = GroundTruth.model_validate(data["ground_truth"])
        return data.get("title", "Án Mạng Bí Ẩn"), data.get("summary", ""), victim, ground_truth

    async def repair_tod(self, victim: Victim, ground_truth: GroundTruth, diagnostic: str) -> Tuple[Victim, GroundTruth]:
        """Localized patch repair for TOD / Crime Time violations (Paper 7)."""
        logger.info(f"[OutlineAgent] Applying localized patch repair: {diagnostic}")
        system_prompt = (
            "You are a Forensic Logic Repair Specialist. "
            "Fix the discrepancy between actual_crime_time and estimated_tod_start/estimated_tod_end based on diagnostic feedback. "
            "Output JSON with corrected 'forensic_data' and 'actual_crime_time'."
        )
        user_prompt = f"""
Current Forensic: {victim.forensic_data.model_dump_json()}
Current Crime Time: {ground_truth.actual_crime_time}
Diagnostic Violation: {diagnostic}
Requirement: The Henssge window in the diagnostic is computed by a physics engine and is authoritative.
Move actual_crime_time inside that window (preferred), or adjust discovery_time / body_temp so that the
recomputed window contains the crime time. Keep body_temp above ambient_temp.
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        if "forensic_data" in data:
            victim.forensic_data = ForensicData.model_validate(data["forensic_data"])
        if "actual_crime_time" in data:
            ground_truth.actual_crime_time = data["actual_crime_time"]
        return victim, ground_truth


class CharacterAgent(BaseAgent):
    """Responsible for generating suspects, personalities, alibis, and secrets."""

    async def generate(self, victim: Victim, ground_truth: GroundTruth, theme: str) -> List[Suspect]:
        system_prompt = (
            "You are a Character Specialist in detective fiction (CharacterAgent). "
            "Generate 3 distinct suspects (SUSP-01, SUSP-02, SUSP-03). "
            "CRITICAL CULTURAL RULE: All suspect names MUST match the cultural background and nationality of the Victim (e.g. if Victim is Vietnamese, ALL suspect names MUST be authentic Vietnamese names like 'Nguyễn Minh Tuấn', 'Trần Hoàng Long', 'Phạm Thị Lan', etc. NEVER use English names like 'Julian Blackwood'). "
            "CRITICAL RULES: "
            "1. SUSP-01 MUST have is_culprit = True (matches GroundTruth). "
            "2. SUSP-02 and SUSP-03 MUST have is_culprit = False. "
            "3. SUSP-01 must provide a fake alibi covering actual_crime_time with a subtle flaw. "
            "4. Each suspect must have a valid motive and alibi_start/alibi_end in HH:MM format. "
            "5. Innocent suspects should have a secret_innocent_fact acting as a red herring."
        )
        user_prompt = f"""
Theme: {theme}
Victim: {victim.name}, {victim.age} tuổi, {victim.occupation}
Ground Truth: Culprit={ground_truth.culprit_id}, Crime Time={ground_truth.actual_crime_time}, Flaw={ground_truth.core_contradiction}
Output JSON:
{{
  "suspects": [
    {{
      "id": "SUSP-01",
      "name": "<Họ tên nghi phạm 1 (Hung thủ - cùng quốc tịch với nạn nhân)>",
      "age": 32,
      "occupation": "<Nghề nghiệp / Quan hệ với nạn nhân>",
      "motive": "<Động cơ gây án>",
      "alibi_start": "21:00",
      "alibi_end": "22:15",
      "alibi_statement": "<Lời khai ngoại phạm che đậy thời điểm gây án nhưng có sơ hở>",
      "is_culprit": true
    }},
    {{
      "id": "SUSP-02",
      "name": "<Họ tên nghi phạm 2 (Người vô tội)>",
      "age": 45,
      "occupation": "<Nghề nghiệp>",
      "motive": "<Động cơ đáng ngờ>",
      "alibi_start": "21:20",
      "alibi_end": "22:00",
      "alibi_statement": "<Lời khai ngoại phạm>",
      "secret_innocent_fact": "<Bí mật cá nhân gây hiểu lầm>",
      "is_culprit": false
    }},
    {{
      "id": "SUSP-03",
      "name": "<Họ tên nghi phạm 3 (Người vô tội)>",
      "age": 28,
      "occupation": "<Nghề nghiệp>",
      "motive": "<Động cơ đáng ngờ>",
      "alibi_start": "20:45",
      "alibi_end": "21:50",
      "alibi_statement": "<Lời khai ngoại phạm>",
      "secret_innocent_fact": "<Bí mật cá nhân gây hiểu lầm>",
      "is_culprit": false
    }}
  ]
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Suspect.model_validate(s) for s in data.get("suspects", [])]

    async def repair_suspects(self, suspects: List[Suspect], ground_truth: GroundTruth, diagnostic: str) -> List[Suspect]:
        """Localized patch repair for duplicate IDs or culprit flags (Paper 7)."""
        logger.info(f"[CharacterAgent] Applying localized patch repair: {diagnostic}")
        system_prompt = (
            "You are a Character Consistency Repair Agent. "
            "Fix suspect IDs or culprit assignment flaws based on the diagnostic feedback. "
            "Output JSON with corrected 'suspects' array. Exactly 1 suspect must have is_culprit=True matching culprit_id."
        )
        user_prompt = f"""
Current Suspects: {[s.model_dump() for s in suspects]}
Ground Truth Culprit ID: {ground_truth.culprit_id}
Diagnostic Violation: {diagnostic}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Suspect.model_validate(s) for s in data.get("suspects", [])]


class ClueAgent(BaseAgent):
    """Responsible for physical evidence, alibi-breaking clues, and red herrings."""

    async def generate(self, victim: Victim, suspects: List[Suspect], ground_truth: GroundTruth, theme: str) -> List[Evidence]:
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        system_prompt = (
            "You are a Forensic Clue Specialist (ClueAgent). "
            "Generate 3 to 4 physical evidences found at the crime scene. "
            "CRITICAL FAIR-PLAY CONSTRAINTS: "
            "1. At least 1 evidence must be CRUCIAL (is_crucial = True). "
            "2. The crucial evidence must indirectly contradict the culprit's alibi statement or prove their presence. "
            "3. At least 1 evidence must be a red herring (is_red_herring = True) pointing suspiciously to an innocent suspect. "
            "4. Do NOT leave obvious direct evidence like an ID card of the killer."
        )
        user_prompt = f"""
Theme: {theme}
Victim: {victim.name}, Wounds: {victim.forensic_data.wound_description}
Culprit: {culprit.id} ({culprit.name}), Alibi: "{culprit.alibi_statement}" [{culprit.alibi_start}-{culprit.alibi_end}]
Ground Truth Contradiction: {ground_truth.core_contradiction}
Output JSON:
{{
  "evidences": [
    {{
      "id": "EV-01",
      "title": "<Tên vật chứng mang tính quyết định>",
      "location": "<Vị trí tại hiện trường>",
      "description": "<Mô tả vật chứng làm sáng tỏ mâu thuẫn trong lời khai của {culprit.name}>",
      "linked_suspect_id": "{culprit.id}",
      "is_crucial": true,
      "is_red_herring": false
    }},
    {{
      "id": "EV-02",
      "title": "<Tên vật chứng đánh lạc hướng>",
      "location": "<Vị trí tại hiện trường>",
      "description": "<Mô tả vật chứng gây hiểu lầm hướng về nghi phạm vô tội>",
      "linked_suspect_id": "SUSP-02",
      "is_crucial": false,
      "is_red_herring": true
    }},
    {{
      "id": "EV-03",
      "title": "<Tên manh mối bổ sung>",
      "location": "<Vị trí tại hiện trường>",
      "description": "<Mô tả dấu vết tại hiện trường>",
      "linked_suspect_id": "SUSP-03",
      "is_crucial": false,
      "is_red_herring": false
    }}
  ]
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Evidence.model_validate(e) for e in data.get("evidences", [])]

    async def repair_clues(self, evidences: List[Evidence], suspects: List[Suspect], ground_truth: GroundTruth, diagnostic: str) -> List[Evidence]:
        """Localized patch repair for missing crucial clue or unbroken alibi (Paper 7)."""
        logger.info(f"[ClueAgent] Applying localized patch repair: {diagnostic}")
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        system_prompt = (
            "You are a Forensic Clue Repair Specialist. "
            "The case validator flagged a flaw: missing crucial clue or unbroken culprit alibi. "
            "Modify or add an evidence item so there is at least one clear crucial clue (is_crucial=True) "
            "that definitively breaks the culprit's alibi. Output JSON with updated 'evidences' array."
        )
        user_prompt = f"""
Culprit: {culprit.id} ({culprit.name})
Culprit Claimed Alibi: "{culprit.alibi_statement}" [{culprit.alibi_start} - {culprit.alibi_end}]
Core Contradiction: {ground_truth.core_contradiction}
Current Evidences: {[e.model_dump() for e in evidences]}
Diagnostic Violation: {diagnostic}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return [Evidence.model_validate(e) for e in data.get("evidences", [])]


class DeductionAgent(BaseAgent):
    """Synthesizes the multi-hop reasoning chain proving solvability (Paper 3 QaAgent)."""

    async def generate(self, victim: Victim, suspects: List[Suspect], evidences: List[Evidence], ground_truth: GroundTruth) -> ReasoningChain:
        culprit = next((s for s in suspects if s.is_culprit), suspects[0])
        crucial_clues = [e.id for e in evidences if e.is_crucial]
        system_prompt = (
            "You are a Chief Detective Logic Synthesizer (DeductionAgent). "
            "Construct a 2-to-3 step Multi-Hop Reasoning Chain proving how the player can crack this case. "
            "Step 1: Notice timeline/forensic contradiction. "
            "Step 2: Connect physical evidence with suspect statement. "
            "Step 3: Expose the culprit's lie and conclude guilt."
        )
        user_prompt = f"""
Victim: {victim.name}, Estimated TOD: {victim.forensic_data.estimated_tod_start} - {victim.forensic_data.estimated_tod_end}
Culprit: {culprit.id} ({culprit.name}), Claim: "{culprit.alibi_statement}"
Crucial Clues Available: {crucial_clues}
Core Contradiction: {ground_truth.core_contradiction}
Output JSON:
{{
  "steps": [
    {{
      "step_number": 1,
      "clue_ids": {crucial_clues},
      "inference": "Báo cáo pháp y xác nhận nạn nhân bị sát hại khoảng {victim.forensic_data.estimated_tod_start}-{victim.forensic_data.estimated_tod_end}.",
      "target_suspect_id": "{culprit.id}"
    }},
    {{
      "step_number": 2,
      "clue_ids": {crucial_clues},
      "inference": "Manh mối tại hiện trường mâu thuẫn trực tiếp với lời khai của {culprit.name}.",
      "target_suspect_id": "{culprit.id}"
    }}
  ],
  "final_conclusion": "{culprit.name} là hung thủ thực sự do lời khai ngoại phạm bị bác bỏ hoàn toàn bởi chứng cứ tại hiện trường.",
  "decisive_contradiction": "{ground_truth.core_contradiction}"
}}
"""
        data = await self._call_llm_json(system_prompt, user_prompt)
        return ReasoningChain.model_validate(data)
