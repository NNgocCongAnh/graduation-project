"""Sequential Multi-Agent & Neuro-Symbolic Case Generation Service.

Orchestrates 4 specialized agents (Paper 3: arXiv:2604.11741):
  - OutlineAgent: Premise, victim forensic data, secret Ground Truth.
  - CharacterAgent: Suspects, motives, alibis, and red-herring secrets.
  - ClueAgent: Physical traces, alibi-breaking crucial clues, red herrings.
  - DeductionAgent: Multi-hop reasoning chain demonstrating solvability.

Features Localized Patch Repair (Paper 7: ConWriter arXiv:2608.05169):
When the Rule-Based Validator identifies logic flaws, targeted feedback is routed
only to the responsible agent for surgical repair, avoiding full-pipeline restarts.
"""

import os
import time
import logging
import asyncio
from typing import Optional, List, Dict, Any
from openai import AsyncOpenAI

from models import (
    CaseDossier, Victim, Suspect, Evidence, GroundTruth, ForensicData,
    ReasoningChain, DeductionStep, GenerationMetadata, ValidationResult, ViolationType
)
from validator import validate_case_diagnostics, validate_case_logic, apply_henssge_tod_window
from agents import OutlineAgent, CharacterAgent, ClueAgent, DeductionAgent

from dotenv import load_dotenv

# Load environment variables from .env in backend directory if present
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

logger = logging.getLogger(__name__)

# LLM Gateway Configuration (Default to local 9Router proxy if not set)
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:20128/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini/gemma-4-31b-it")


class CaseGeneratorService:
    """Service orchestrating specialized agents and neuro-symbolic localized repair."""

    def __init__(self, api_base: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.model = model or LLM_MODEL

        # Smart routing: auto-route local Ollama models to Ollama daemon
        if not api_base:
            if "gemma4:e4b" in self.model or "ollama" in self.model:
                self.api_base = "http://localhost:11434/v1"
                self.api_key = api_key or "ollama"
            else:
                self.api_base = LLM_API_BASE
                self.api_key = api_key or LLM_API_KEY
        else:
            self.api_base = api_base
            self.api_key = api_key or LLM_API_KEY

        # Initialize Async OpenAI Client
        self.client = AsyncOpenAI(
            base_url=self.api_base,
            api_key=self.api_key
        )

        # Initialize Specialized Agents (Paper 3)
        self.outline_agent = OutlineAgent(self.client, self.model)
        self.character_agent = CharacterAgent(self.client, self.model)
        self.clue_agent = ClueAgent(self.client, self.model)
        self.deduction_agent = DeductionAgent(self.client, self.model)

    def update_config(self, model: Optional[str] = None, api_base: Optional[str] = None, api_key: Optional[str] = None):
        """Update active model, api_base, and api_key dynamically at runtime."""
        if model and model.strip():
            self.model = model.strip()
        if api_base and api_base.strip():
            self.api_base = api_base.strip()
        if api_key and api_key.strip():
            self.api_key = api_key.strip()

        self.client = AsyncOpenAI(
            base_url=self.api_base,
            api_key=self.api_key
        )
        self.outline_agent = OutlineAgent(self.client, self.model)
        self.character_agent = CharacterAgent(self.client, self.model)
        self.clue_agent = ClueAgent(self.client, self.model)
        self.deduction_agent = DeductionAgent(self.client, self.model)
        logger.info(f"Updated LLM Config -> Model: '{self.model}', Base: '{self.api_base}'")

    async def _generate_case_monolithic(self, theme: str) -> CaseDossier:
        """Generate full case dossier using a single monolithic prompt without multi-agent decomposition (Ablation Config 1)."""
        start_total = time.time()
        system_prompt = (
            "You are an End-to-End Mystery Case Generator. "
            "Generate a complete, cohesive locked-room mystery case dossier in a single JSON payload. "
            "The JSON must include: title, summary, victim (with complete forensic_data), "
            "suspects (array of 3 suspects with alibis, motives, statements), "
            "evidences (array of 5 evidences: 1 timing/baseline, 2 red herrings, 1 alibi-breaking crucial clue, 1 weapon), "
            "ground_truth (actual_crime_time, culprit_id, motive, method, core_contradiction), "
            "and reasoning_chain (4 deduction steps, final_conclusion, decisive_contradiction). "
            "Make sure the suspect alibis and crime times are consistent."
        )
        user_prompt = f"""Theme: {theme}\nOutput a complete CaseDossier JSON adhering strictly to the schema."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        total_lat = round(time.time() - start_total, 2)

        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if getattr(response, "usage", None):
            prompt_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
            completion_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            total_tokens = getattr(response.usage, "total_tokens", 0) or 0

        raw_text = response.choices[0].message.content or "{}"
        clean_text = self.outline_agent._clean_json_string(raw_text)
        import json
        data = json.loads(clean_text)

        if "case_id" not in data:
            data["case_id"] = f"CASE-{os.urandom(3).hex().upper()}"
        dossier = CaseDossier.model_validate(data)

        diag = validate_case_diagnostics(dossier)
        dossier.metadata = GenerationMetadata(
            model_name=self.model,
            pipeline_version="monolithic-single-prompt",
            config_mode="monolithic",
            agent_latencies={"Monolithic": total_lat},
            agent_models={"Monolithic": self.model},
            fallback_triggered=False,
            used_fallback_sample=False,
            total_latency=total_lat,
            patch_retries=0,
            validator_score=1.0 if diag.is_valid else 0.0,
            token_usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "patch_tokens": 0
            }
        )
        return dossier

    async def generate_case(
        self,
        theme: str = "Bí ẩn Biệt thự Cổ (Locked-Room Mystery)",
        max_retries: int = 2,
        enable_post_processing: bool = True,
        enable_patch_repair: bool = True,
        mode: str = "pipeline"
    ) -> CaseDossier:
        """Generate a logically sound Case Dossier via Multi-Agent pipeline with Localized Repair."""
        if mode == "monolithic":
            return await self._generate_case_monolithic(theme)

        start_total = time.time()
        agent_latencies: Dict[str, float] = {}
        patch_retries = 0
        patch_prompt_tokens = 0
        patch_completion_tokens = 0
        patch_payload_tokens = 0

        for attempt in range(1, max_retries + 1):
            logger.info(f"Multi-Agent Generation Run {attempt}/{max_retries} for theme: '{theme}' (Model: {self.model})")
            try:
                # 1. OutlineAgent: Premise & Ground Truth
                t0 = time.time()
                title, summary, victim, ground_truth = await self.outline_agent.generate(theme)
                if enable_post_processing:
                    # Symbolic engine owns the TOD window: derive it from Henssge, not from the LLM.
                    apply_henssge_tod_window(victim.forensic_data)
                agent_latencies["OutlineAgent"] = round(time.time() - t0, 2)

                # 2. CharacterAgent: Suspects & Alibis
                t1 = time.time()
                suspects = await self.character_agent.generate(
                    victim, ground_truth, theme, enable_post_processing=enable_post_processing
                )
                agent_latencies["CharacterAgent"] = round(time.time() - t1, 2)

                # 3. ClueAgent: Evidences & Red Herrings
                t2 = time.time()
                evidences = await self.clue_agent.generate(victim, suspects, ground_truth, theme)
                agent_latencies["ClueAgent"] = round(time.time() - t2, 2)

                # Assemble preliminary candidate dossier
                case_id = f"CASE-{os.urandom(3).hex().upper()}"
                candidate_dossier = CaseDossier(
                    case_id=case_id,
                    title=title,
                    summary=summary,
                    victim=victim,
                    suspects=suspects,
                    evidences=evidences,
                    ground_truth=ground_truth
                )

                # 4. Neuro-Symbolic Validator & Localized Patch Repair (Paper 7)
                diag = validate_case_diagnostics(candidate_dossier)
                if not diag.is_valid and enable_patch_repair:
                    logger.warning(f"Initial validation flagged {len(diag.violations)} violations. Initiating Localized Patch Repair...")
                    # Localized repair loop: fix only the flawed component
                    for violation in diag.violations:
                        feedback = violation.message
                        if violation.component == "clue":
                            evidences = await self.clue_agent.repair_clues(evidences, suspects, ground_truth, feedback)
                            patch_prompt_tokens += self.clue_agent.last_usage.get("prompt_tokens", 0)
                            patch_completion_tokens += self.clue_agent.last_usage.get("completion_tokens", 0)
                            patch_payload_tokens += self.clue_agent.last_payload_tokens
                            patch_retries += 1
                        elif violation.component == "character":
                            suspects = await self.character_agent.repair_suspects(suspects, ground_truth, feedback)
                            patch_prompt_tokens += self.character_agent.last_usage.get("prompt_tokens", 0)
                            patch_completion_tokens += self.character_agent.last_usage.get("completion_tokens", 0)
                            patch_payload_tokens += self.character_agent.last_payload_tokens
                            patch_retries += 1
                        elif violation.component == "outline":
                            victim, ground_truth = await self.outline_agent.repair_tod(victim, ground_truth, feedback)
                            if enable_post_processing:
                                apply_henssge_tod_window(victim.forensic_data)
                                if ground_truth.actual_crime_time:
                                    try:
                                        c_h, c_m = map(int, ground_truth.actual_crime_time.split(':'))
                                        c_tot = c_h * 60 + c_m
                                        for s in suspects:
                                            if s.is_culprit:
                                                s_h, s_m = map(int, s.alibi_start.split(':'))
                                                e_h, e_m = map(int, s.alibi_end.split(':'))
                                                if not (s_h * 60 + s_m <= c_tot <= e_h * 60 + e_m):
                                                    s.alibi_start = f"{max(0, c_tot - 25) // 60:02d}:{max(0, c_tot - 25) % 60:02d}"
                                                    s.alibi_end = f"{min(1439, c_tot + 35) // 60:02d}:{min(1439, c_tot + 35) % 60:02d}"
                                                    s.timeline_claimed = f"{s.alibi_start} - {s.alibi_end}"
                                    except Exception:
                                        pass
                            patch_prompt_tokens += self.outline_agent.last_usage.get("prompt_tokens", 0)
                            patch_completion_tokens += self.outline_agent.last_usage.get("completion_tokens", 0)
                            patch_payload_tokens += self.outline_agent.last_payload_tokens
                            patch_retries += 1

                    # Re-assemble and re-validate
                    candidate_dossier.victim = victim
                    candidate_dossier.suspects = suspects
                    candidate_dossier.evidences = evidences
                    candidate_dossier.ground_truth = ground_truth
                    diag = validate_case_diagnostics(candidate_dossier)

                # 5. DeductionAgent: Synthesize Multi-Hop Reasoning Chain (Paper 3)
                t3 = time.time()
                try:
                    reasoning_chain = await self.deduction_agent.generate(victim, suspects, evidences, ground_truth, theme)
                except Exception as ex:
                    logger.warning(f"DeductionAgent reasoning chain generation skipped ({ex}).")
                    reasoning_chain = None
                agent_latencies["DeductionAgent"] = round(time.time() - t3, 2)

                # Attach Telemetry Metadata
                total_latency = round(time.time() - start_total, 2)
                agent_models = {
                    "OutlineAgent": self.outline_agent.last_used_model,
                    "CharacterAgent": self.character_agent.last_used_model,
                    "ClueAgent": self.clue_agent.last_used_model,
                    "DeductionAgent": self.deduction_agent.last_used_model if reasoning_chain is not None else "skipped",
                }
                fallback_triggered = any([
                    self.outline_agent.fallback_used,
                    self.character_agent.fallback_used,
                    self.clue_agent.fallback_used,
                    self.deduction_agent.fallback_used if reasoning_chain is not None else False,
                ])

                gen_prompt_tokens = (
                    self.outline_agent.last_usage.get("prompt_tokens", 0) +
                    self.character_agent.last_usage.get("prompt_tokens", 0) +
                    self.clue_agent.last_usage.get("prompt_tokens", 0) +
                    (self.deduction_agent.last_usage.get("prompt_tokens", 0) if reasoning_chain is not None else 0)
                )
                gen_completion_tokens = (
                    self.outline_agent.last_usage.get("completion_tokens", 0) +
                    self.character_agent.last_usage.get("completion_tokens", 0) +
                    self.clue_agent.last_usage.get("completion_tokens", 0) +
                    (self.deduction_agent.last_usage.get("completion_tokens", 0) if reasoning_chain is not None else 0)
                )

                config_mode = "full_pipeline"
                if not enable_post_processing and not enable_patch_repair:
                    config_mode = "pipeline_no_postproc"
                elif enable_post_processing and not enable_patch_repair:
                    config_mode = "pipeline_no_repair"

                candidate_dossier.reasoning_chain = reasoning_chain
                candidate_dossier.metadata = GenerationMetadata(
                    model_name=self.model,
                    pipeline_version="2.0-neuro-symbolic",
                    config_mode=config_mode,
                    agent_latencies=agent_latencies,
                    agent_models=agent_models,
                    fallback_triggered=fallback_triggered,
                    used_fallback_sample=False,
                    total_latency=total_latency,
                    patch_retries=patch_retries,
                    validator_score=1.0 if diag.is_valid else 0.5,
                    token_usage={
                        "gen_prompt_tokens": gen_prompt_tokens,
                        "gen_completion_tokens": gen_completion_tokens,
                        "gen_total_tokens": gen_prompt_tokens + gen_completion_tokens,
                        "patch_prompt_tokens": patch_prompt_tokens,
                        "patch_completion_tokens": patch_completion_tokens,
                        "patch_total_tokens": patch_prompt_tokens + patch_completion_tokens,
                        "patch_payload_tokens": patch_payload_tokens,
                        "avg_patch_payload_tokens": round(patch_payload_tokens / patch_retries, 1) if patch_retries else 0.0,
                        "total_tokens": gen_prompt_tokens + gen_completion_tokens + patch_prompt_tokens + patch_completion_tokens,
                        "per_agent": {
                            "OutlineAgent": self.outline_agent.last_usage,
                            "CharacterAgent": self.character_agent.last_usage,
                            "ClueAgent": self.clue_agent.last_usage,
                            "DeductionAgent": self.deduction_agent.last_usage if reasoning_chain is not None else {}
                        }
                    }
                )

                logger.info(
                    f"Successfully generated case '{case_id}' in {total_latency}s "
                    f"(Patch retries: {patch_retries}, Logic valid: {diag.is_valid})."
                )
                return candidate_dossier

            except Exception as e:
                logger.error(f"Error during agentic pipeline execution on attempt {attempt}: {e}")

        # Fallback to offline deterministic sample case
        logger.info("Using high-quality deterministic seed case fallback.")
        sample = self.get_sample_case()
        sample.metadata = GenerationMetadata(
            model_name=self.model,
            pipeline_version="fallback-seed",
            config_mode="fallback",
            fallback_triggered=True,
            used_fallback_sample=True,
            total_latency=round(time.time() - start_total, 2),
            patch_retries=0,
            validator_score=1.0
        )
        return sample

    @staticmethod
    def get_sample_case() -> CaseDossier:
        """Return a verified, deterministic sample case for offline testing & WebGL development."""
        return CaseDossier(
            case_id="CASE-2026-001",
            title="Bí ẩn Biệt thự Blackwood",
            summary="Vụ án mạng trong thư phòng khóa kín tại tầng hai biệt thự cổ Blackwood giữa đêm mưa bão.",
            victim=Victim(
                name="Arthur Blackwood",
                age=62,
                occupation="Chủ sở hữu trang viên & Doanh nhân",
                gender="Nam",
                residence="Biệt thự cổ Blackwood, Hạt Sussex",
                forensic_data=ForensicData(
                    ambient_temp=21.0,
                    body_temp=31.2,
                    livor_mortis_state="Hoen tử thi tím sẫm cố định ở vùng lưng, mông và mặt sau bắp đùi. Dùng ngón tay ấn mạnh không đổi màu, xác nhận thi thể nằm ngửa nguyên trạng từ khi tử vong.",
                    rigor_mortis_state="Co cứng toàn phần (Full Rigor Mortis) ở cơ hàm, cổ, các khớp ngón tay và khớp gối, không thể gập mở tự nhiên.",
                    wound_description="Vết đâm trực diện khoang liên sườn 4-5 bên trái dài 2.0cm, sâu khoảng 8.5cm, xuyên thủng màng ngoài tim và thất trái, làm rách quai động mạch chủ ngực.",
                    cause_of_death="Sốc mất máu cấp tính do tổn thương thấu tim (Acute Hemorrhagic Shock).",
                    manner_of_death="Vụ án mạng sát hại (Homicide).",
                    clothing_state="Nạn nhân mặc đầy đủ áo sơ mi lụa, áo len cashmere và quần âu ấm, không có dấu hiệu bị xé rách trang phục.",
                    # Henssge: 31.2°C body / 21.0°C room / 70 kg / C=1.0 -> t* = 10.9 h before 08:30
                    estimated_tod_start="20:06",
                    estimated_tod_end="23:06",
                    body_weight_kg=70.0,
                    cooling_factor=1.0,
                    discovery_time="08:30"
                )
            ),
            suspects=[
                Suspect(
                    id="SUSP-01",
                    name="Quản gia William Vance",
                    age=55,
                    occupation="Quản gia trưởng",
                    gender="Nam",
                    relationship_to_victim="Quản gia gia tộc Blackwood (25 năm phục vụ)",
                    residence="Gian phòng quản gia cạnh bếp tầng trệt",
                    motive="Bị dọa đuổi việc và tước quyền thừa kế sau khi làm thất thoát tài sản gia tộc.",
                    statement="Tối hôm đó tôi nhận lệnh mang trà lên lúc 21:00 nhưng ngài Arthur bảo không cần. Tôi quay xuống gian bếp phụ trách đun nước trên bếp lò than và lau dọn bộ ấm chén bạc. Suốt từ 21:00 đến 22:30 tôi chỉ ở dưới bếp một mình, liên tục chụm lửa đun trà.",
                    timeline_claimed="21:00 - 22:30 (Tại gian bếp phụ tầng trệt)",
                    interview_notes="Đối tượng tỏ ra điềm tĩnh nhưng liên tục giấu bàn tay phải vào túi tạp dề vải cotton thô dệt chéo màu trắng ngà. Ngón trỏ bàn tay phải có vết cứa da mới còn rớm máu, đối tượng khai bị trượt dao khi gọt hoa quả dưới bếp. Đối tượng có Nhóm máu O.",
                    alibi_start="21:00",
                    alibi_end="22:30",
                    alibi_statement="Khai rằng suốt từ 21:00 đến 22:30 chỉ ở dưới bếp phụ trách chuẩn bị trà đêm một mình.",
                    secret_innocent_fact=None,
                    is_culprit=True,
                    image_url="/static/assets/suspects/butler_male_50s.png"
                ),
                Suspect(
                    id="SUSP-02",
                    name="Bác sĩ Julian Grey",
                    age=42,
                    occupation="Bác sĩ gia đình",
                    gender="Nam",
                    relationship_to_victim="Bác sĩ điều trị riêng của Nạn nhân (5 năm)",
                    residence="Khu nhà phụ phía tây trang viên Blackwood",
                    motive="Bị nạn nhân phát hiện kê đơn thuốc an thần khống nhằm trục lợi bảo hiểm y tế.",
                    statement="Sau khi dùng bữa tối lúc 20:00, tôi xuống phòng khách tầng trệt để thưởng rượu và chơi cờ cùng một vị khách mời. Chúng tôi ngồi tại đó liên tục từ 21:15 đến tận 22:45. Tôi không hề lên tầng hai vào đêm đó.",
                    timeline_claimed="21:15 - 22:45 (Tại phòng khách tầng trệt)",
                    interview_notes="Vị khách chơi cờ cùng xác nhận bác sĩ có mặt hầu hết thời gian, tuy nhiên vào khoảng 21:30 bác sĩ có rời bàn cờ khoảng 10 phút ra hành lang với vẻ mặt bối rối. Đối tượng có Nhóm máu B.",
                    alibi_start="21:15",
                    alibi_end="22:45",
                    alibi_statement="Đang chơi cờ và thưởng rượu cùng khách mời tại phòng khách tầng trệt.",
                    secret_innocent_fact="Đang lén tiêu hủy hồ sơ bảo hiểm cá nhân trong lò sưởi lúc 21:30",
                    is_culprit=False,
                    image_url="/static/assets/suspects/businessman_male_50s.png"
                ),
                Suspect(
                    id="SUSP-03",
                    name="Cháu gái Eleanor Blackwood",
                    age=26,
                    occupation="Nghệ sĩ dương cầm",
                    gender="Nữ",
                    relationship_to_victim="Cháu gái ruột của Nạn nhân",
                    residence="Phòng ngủ phía đông lầu hai (cùng tầng với thư phòng)",
                    motive="Cần tiền mặt gấp để trang trải nợ cờ bạc trước hạn chót tuần sau.",
                    statement="Tôi ở trong phòng nhạc tập luyện dương cầm liên tục từ 20:45 đến 22:00. Sau đó tôi có gọi điện thoại đường dài cho người hướng dẫn hòa nhạc tại London.",
                    timeline_claimed="20:45 - 22:00 (Tại phòng nhạc phía đông)",
                    interview_notes="Người hầu xác nhận có nghe tiếng đàn piano. Tổng đài bưu điện ghi nhận cuộc gọi đường dài của cô từ 20:28 đến 20:50. Giày lụa có dính bùn đất do chập tối (19:45) từng trèo lên ban công tìm bản sao di chúc nhưng then chốt cửa bị khóa trong. Đối tượng có Nhóm máu A.",
                    alibi_start="20:45",
                    alibi_end="22:00",
                    alibi_statement="Luyện đàn tại phòng nhạc phía đông, có người hầu nghe thấy tiếng đàn piano liên tục.",
                    secret_innocent_fact="Lén sao chép bản di chúc cũ",
                    is_culprit=False,
                    image_url="/static/assets/suspects/female_30s.png"
                )
            ],
            evidences=[
                Evidence(
                    id="EV-01",
                    title="Đồng hồ bỏ túi bị vỡ kẹt kim 21:40",
                    location="Dưới chân bàn làm việc trong thư phòng",
                    description="Mặt kính pha lê chịu lực bị đập vỡ vụn góc 2 giờ, kim giờ và kim phút kẹt cứng chính xác tại 21:40.",
                    is_weapon=False,
                    fingerprint_analysis="Phát hiện một phần dấu vân tay ngón cái mờ của Nạn nhân trên núm vặn dây cót. Không tìm thấy bất kỳ dấu vân tay lạ nào khác.",
                    blood_dna_analysis="Không phát hiện dấu vết máu hay dịch sinh học.",
                    physical_condition="Mặt kính pha lê chịu lực bị va đập vỡ vụn, kim đồng hồ dừng tại 21:40. Bộ máy cơ học bên trong còn nguyên vẹn, dây cót chưa hề bị đứt, cơ cấu hồi còn đủ năng lượng hoạt động khi kiểm tra chuyển động (chứng tỏ đồng hồ bị ngoại lực tác động làm kẹt kim cố ý chứ không phải chết máy tự nhiên).",
                    linked_suspect_id=None,
                    is_crucial=True,
                    is_red_herring=False,
                    image_url="/static/assets/evidences/pocket_watch_broken.png"
                ),
                Evidence(
                    id="EV-02",
                    title="Dao rạch thư bạc dính vết máu",
                    location="Trong ống thông gió gian bếp",
                    description="Dao rạch thư mạ bạc khắc gia huy Blackwood giấu sâu trong ống khói thông gió gian bếp, dính vệt máu khô.",
                    is_weapon=True,
                    fingerprint_analysis="Cán dao có nhiều vết miết chà xát ngang dọc bằng sợi vải thô lau chùi dấu vết. Tại khe khâu nối giữa cán và lưỡi dao phát hiện một sợi vải cotton dệt chéo màu trắng ngà bị kẹt lại.",
                    blood_dna_analysis="Vệt máu khô trên mũi dao thuộc Nhóm máu A (trùng khớp ADN của Nạn nhân Arthur Blackwood). Trên chuôi dao phát hiện 2 vi vết máu li ti khô thuộc Nhóm máu O (nghi vết cắt do giằng co).",
                    physical_condition="Dao rạch thư lưỡi thép không gỉ mạ bạc dài 14.5cm, rộng bản 1.8cm, chuôi đúc nổi gia huy Blackwood. Mũi dao nhọn tương thích hoàn toàn với vết đâm thấu ngực liên sườn 4-5. Được tìm thấy giấu kín trong ống thông gió gian bếp tầng trệt mà chỉ người ở bếp mới tiếp cận được.",
                    linked_suspect_id="SUSP-01",
                    is_crucial=True,
                    is_red_herring=False,
                    image_url="/static/assets/evidences/evidence_knife.png"
                ),
                Evidence(
                    id="EV-03",
                    title="Hồ sơ y tế cháy dở & Lọ an thần",
                    location="Trong lò sưởi phòng khách tầng trệt",
                    description="Lọ thuốc an thần Diazepam 5mg do Bác sĩ gia đình kê đơn, còn nguyên niêm phong màng nhôm bên cạnh các trang giấy sổ sách y bạ cháy xém.",
                    is_weapon=False,
                    fingerprint_analysis="Phát hiện dấu vân tay ngón trỏ của bác sĩ điều trị trên nhãn thuốc và mảnh giấy cháy dở.",
                    blood_dna_analysis="Không phát hiện dấu vết máu.",
                    physical_condition="Lọ thủy tinh màu hổ phách chứa 20 viên Diazepam 5mg. Lớp màng nhôm niêm phong miệng lọ còn nguyên vẹn, chứng minh thuốc chưa từng được mở nắp sử dụng và nạn nhân không hề bị đầu độc hay chuốc thuốc trước khi chết.",
                    linked_suspect_id="SUSP-02",
                    is_crucial=False,
                    is_red_herring=True,
                    image_url="/static/assets/evidences/evidence_sedative.png"
                )
            ],
            ground_truth=GroundTruth(
                culprit_id="SUSP-01",
                actual_crime_time="21:40",
                murder_weapon="Dao rạch thư bạc mạ gia huy Blackwood",
                core_contradiction="Quản gia William Vance khai suốt từ 21:00 đến 22:30 chỉ ở dưới bếp phụ trách đun nước pha trà một mình. Tuy nhiên, hung khí dao rạch thư dính máu Nhóm A của nạn nhân được tìm thấy giấu trong ống thông gió gian bếp. Chuôi dao dính máu Nhóm O và sợi vải tạp dề trắng ngà, trùng khớp với ngón tay trỏ bị cứa rách rớm máu và tạp dề của William Vance."
            ),
            reasoning_chain=ReasoningChain(
                steps=[
                    DeductionStep(
                        step_number=1,
                        clue_ids=["EV-01"],
                        inference="Đồng hồ vỡ xác nhận án mạng xảy ra vào khoảng 21:40, nằm trong khung giờ tử vong pháp y Henssge (20:06 - 23:06).",
                        target_suspect_id="SUSP-01"
                    ),
                    DeductionStep(
                        step_number=2,
                        clue_ids=["EV-02"],
                        inference="Dao rạch thư hung khí dính máu nạn nhân được giấu trong ống thông gió tại gian bếp nơi Quản gia William khai đang ở một mình; chuôi dao dính máu Nhóm O và sợi vải tạp dề trùng khớp vết thương mới ở ngón tay của ông ta.",
                        target_suspect_id="SUSP-01"
                    )
                ],
                final_conclusion="Quản gia William Vance đã lợi dụng việc chuẩn bị trà để lẻn lên thư phòng gây án lúc 21:40 rồi phi tang hung khí vào ống thông gió gian bếp.",
                decisive_contradiction="Lời khai ở bếp pha trà liên tục mâu thuẫn với việc hung khí dính máu được giấu ngay tại gian bếp, mang vết máu Nhóm O và sợi chỉ tạp dề trùng khớp với William Vance."
            ),
            metadata=GenerationMetadata(
                model_name="gh/gpt-4o",
                pipeline_version="2.0-neuro-symbolic",
                agent_latencies={"OutlineAgent": 10.2, "CharacterAgent": 11.5, "ClueAgent": 14.1, "DeductionAgent": 5.8},
                agent_models={
                    "OutlineAgent": "gh/gpt-4o",
                    "CharacterAgent": "gh/gpt-4o",
                    "ClueAgent": "gh/gpt-4o",
                    "DeductionAgent": "gh/gpt-4o"
                },
                fallback_triggered=False,
                total_latency=41.6,
                patch_retries=0,
                validator_score=1.0
            )
        )
