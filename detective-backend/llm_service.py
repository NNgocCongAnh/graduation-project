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
from validator import validate_case_diagnostics, validate_case_logic
from agents import OutlineAgent, CharacterAgent, ClueAgent, DeductionAgent

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)

# LLM Gateway Configuration (Default to local 9Router proxy if not set)
LLM_API_BASE = os.getenv("LLM_API_BASE", "http://localhost:20128/v1")
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-9router-local")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-2-9b-it")


class CaseGeneratorService:
    """Service orchestrating specialized agents and neuro-symbolic localized repair."""

    def __init__(self, api_base: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_base = api_base or LLM_API_BASE
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL

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

    async def generate_case(self, theme: str = "Bí ẩn Biệt thự Cổ (Locked-Room Mystery)", max_retries: int = 2) -> CaseDossier:
        """Generate a logically sound Case Dossier via Multi-Agent pipeline with Localized Repair."""
        start_total = time.time()
        agent_latencies: Dict[str, float] = {}
        patch_retries = 0

        for attempt in range(1, max_retries + 1):
            logger.info(f"Multi-Agent Generation Run {attempt}/{max_retries} for theme: '{theme}' (Model: {self.model})")
            try:
                # 1. OutlineAgent: Premise & Ground Truth
                t0 = time.time()
                title, summary, victim, ground_truth = await self.outline_agent.generate(theme)
                agent_latencies["OutlineAgent"] = round(time.time() - t0, 2)

                # 2. CharacterAgent: Suspects & Alibis
                t1 = time.time()
                suspects = await self.character_agent.generate(victim, ground_truth, theme)
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
                if not diag.is_valid:
                    logger.warning(f"Initial validation flagged {len(diag.violations)} violations. Initiating Localized Patch Repair...")
                    # Localized repair loop: fix only the flawed component
                    for violation in diag.violations:
                        feedback = violation.message
                        if violation.component == "clue":
                            evidences = await self.clue_agent.repair_clues(evidences, suspects, ground_truth, feedback)
                            patch_retries += 1
                        elif violation.component == "character":
                            suspects = await self.character_agent.repair_suspects(suspects, ground_truth, feedback)
                            patch_retries += 1
                        elif violation.component == "outline":
                            victim, ground_truth = await self.outline_agent.repair_tod(victim, ground_truth, feedback)
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
                    reasoning_chain = await self.deduction_agent.generate(victim, suspects, evidences, ground_truth)
                except Exception as ex:
                    logger.warning(f"DeductionAgent reasoning chain generation skipped ({ex}).")
                    reasoning_chain = None
                agent_latencies["DeductionAgent"] = round(time.time() - t3, 2)

                # Attach Telemetry Metadata
                total_latency = round(time.time() - start_total, 2)
                candidate_dossier.reasoning_chain = reasoning_chain
                candidate_dossier.metadata = GenerationMetadata(
                    model_name=self.model,
                    pipeline_version="2.0-neuro-symbolic",
                    agent_latencies=agent_latencies,
                    total_latency=total_latency,
                    patch_retries=patch_retries,
                    validator_score=1.0 if diag.is_valid else 0.5
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
        return self.get_sample_case()

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
                forensic_data=ForensicData(
                    ambient_temp=21.0,
                    body_temp=31.2,
                    livor_mortis_state="Hoen tử thi cố định ở vùng lưng, không đổi màu khi ấn mạnh.",
                    wound_description="Vết đâm sâu 8cm xuyên qua khoang ngực trái gây mất máu cấp.",
                    estimated_tod_start="21:00",
                    estimated_tod_end="22:30"
                )
            ),
            suspects=[
                Suspect(
                    id="SUSP-01",
                    name="Quản gia William Vance",
                    age=55,
                    occupation="Quản gia trưởng",
                    motive="Bị dọa đuổi việc và tước quyền thừa kế sau khi làm thất thoát tài sản.",
                    alibi_start="21:00",
                    alibi_end="22:30",
                    alibi_statement="Khai rằng suốt từ 21:00 đến 22:30 chỉ ở dưới bếp phụ trách chuẩn bị trà đêm một mình.",
                    is_culprit=True
                ),
                Suspect(
                    id="SUSP-02",
                    name="Bác sĩ Julian Grey",
                    age=40,
                    occupation="Bác sĩ gia đình",
                    motive="Bị nạn nhân phát hiện kê đơn thuốc sai quy cách nhằm trục lợi bảo hiểm.",
                    alibi_start="21:15",
                    alibi_end="22:45",
                    alibi_statement="Đang chơi cờ và thưởng rượu cùng khách mời tại phòng khách tầng trệt.",
                    secret_innocent_fact="Đang lén tiêu hủy hồ sơ bảo hiểm cá nhân",
                    is_culprit=False
                ),
                Suspect(
                    id="SUSP-03",
                    name="Cháu gái Eleanor Blackwood",
                    age=26,
                    occupation="Nghệ sĩ dương cầm",
                    motive="Cần tiền trả nợ cờ bạc khẩn cấp trước hạn chót tuần sau.",
                    alibi_start="20:45",
                    alibi_end="22:00",
                    alibi_statement="Luyện đàn tại phòng nhạc phía đông, có người hầu nghe thấy tiếng đàn piano liên tục.",
                    secret_innocent_fact="Lén sao chép bản di chúc cũ",
                    is_culprit=False
                )
            ],
            evidences=[
                Evidence(
                    id="EV-01",
                    title="Đồng hồ bỏ túi bị vỡ",
                    location="Dưới gầm bàn làm việc thư phòng",
                    description="Mặt kính pha lê bị đập vỡ, kim đồng hồ dừng lại chính xác tại 21:40.",
                    linked_suspect_id=None,
                    is_crucial=True,
                    is_red_herring=False
                ),
                Evidence(
                    id="EV-02",
                    title="Dao rạch thư bạc dính vết máu",
                    location="Trong ống thông gió gian bếp",
                    description="Dao rạch thư mạ bạc khắc gia huy William, có vết máu khô khớp ADN nạn nhân.",
                    linked_suspect_id="SUSP-01",
                    is_crucial=True,
                    is_red_herring=False
                ),
                Evidence(
                    id="EV-03",
                    title="Hộp thuốc an thần dở dang",
                    location="Bàn trang điểm phòng khách",
                    description="Lọ thuốc an thần do Bác sĩ Julian kê đơn sáng cùng ngày, chưa bóc seal.",
                    linked_suspect_id="SUSP-02",
                    is_crucial=False,
                    is_red_herring=True
                )
            ],
            ground_truth=GroundTruth(
                culprit_id="SUSP-01",
                actual_crime_time="21:40",
                murder_weapon="Dao rạch thư bạc mạ gia huy",
                core_contradiction="Quản gia William khai ở bếp nấu nước pha trà từ 21:00-22:30, nhưng bếp lò lạnh ngắt và dao hung khí dính máu được giấu trong ống thông gió bếp sau khi gây án lúc 21:40."
            ),
            reasoning_chain=ReasoningChain(
                steps=[
                    DeductionStep(
                        step_number=1,
                        clue_ids=["EV-01"],
                        inference="Đồng hồ vỡ xác nhận án mạng xảy ra vào lúc 21:40, hoàn toàn trùng khớp với cửa sổ tử vong pháp y 21:00-22:30.",
                        target_suspect_id="SUSP-01"
                    ),
                    DeductionStep(
                        step_number=2,
                        clue_ids=["EV-02"],
                        inference="Dao rạch thư dính máu hung khí được tìm thấy trong ống thông gió tại gian bếp nơi Quản gia William khai đang ở một mình.",
                        target_suspect_id="SUSP-01"
                    )
                ],
                final_conclusion="Quản gia William Vance đã lợi dụng việc chuẩn bị trà để lẻn lên thư phòng gây án lúc 21:40 rồi phi tang hung khí vào ống thông gió.",
                decisive_contradiction="Lời khai ở bếp pha trà liên tục mâu thuẫn với việc hung khí dính máu được giấu ngay tại gian bếp."
            ),
            metadata=GenerationMetadata(
                model_name="deterministic-seed",
                pipeline_version="2.0-neuro-symbolic",
                agent_latencies={"OutlineAgent": 0.0, "CharacterAgent": 0.0, "ClueAgent": 0.0, "DeductionAgent": 0.0},
                total_latency=0.0,
                patch_retries=0,
                validator_score=1.0
            )
        )
