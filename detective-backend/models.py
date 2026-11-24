"""Pydantic v2 Data Models and Schemas for AI Detective Game Engine.

Defines strictly typed structures for Victims, Suspects, Evidences,
Forensic Data, Ground Truth, Multi-hop Reasoning Chains (Paper 3),
Neuro-Symbolic Constraint Diagnostics (Paper 7), Case Dossiers, and API payloads.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


def _normalize_hhmm(v: str) -> str:
    """Validate a 24-hour 'HH:MM' string and zero-pad it."""
    parts = str(v).strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format '{v}'. Expected 'HH:MM'.")
    hours, minutes = int(parts[0]), int(parts[1])
    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(f"Time '{v}' out of range (00:00 - 23:59).")
    return f"{hours:02d}:{minutes:02d}"


class ForensicData(BaseModel):
    """Forensic biological data and post-mortem findings."""
    ambient_temp: float = Field(..., description="Ambient temperature of the crime scene in Celsius (°C).")
    body_temp: float = Field(..., description="Body core temperature upon discovery in Celsius (°C).")
    livor_mortis_state: str = Field(..., description="State of livor mortis (e.g., 'Hoen ố cố định ở lưng', 'Blanchable on pressure').")
    wound_description: str = Field(..., description="Detailed description of fatal and non-fatal wounds.")
    estimated_tod_start: str = Field(..., description="Estimated start time of death (HH:MM, 24-hour format).")
    estimated_tod_end: str = Field(..., description="Estimated end time of death (HH:MM, 24-hour format).")
    # Henssge (1988) nomogram inputs. Defaults = standard adult, light clothing, still air.
    body_weight_kg: float = Field(default=70.0, ge=30.0, le=200.0, description="Body mass M (kg) for the Henssge cooling constant.")
    cooling_factor: float = Field(default=1.0, ge=0.3, le=2.0, description="Henssge corrective factor C (1.0 clothed/still air, 0.75-0.9 naked, 1.1-1.2 covered, 0.5 still water).")
    discovery_time: Optional[str] = Field(default=None, description="Time the body was found and rectal temperature measured (HH:MM). Anchors the Henssge TOD window.")
    rigor_mortis_state: Optional[str] = Field(default=None, description="Detailed rigor mortis progression.")
    cause_of_death: Optional[str] = Field(default=None, description="Formal forensic cause of death.")
    manner_of_death: Optional[str] = Field(default=None, description="Forensic manner of death (Homicide, etc.).")
    clothing_state: Optional[str] = Field(default=None, description="Victim clothing and textile status.")

    @field_validator("discovery_time")
    @classmethod
    def validate_discovery_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not str(v).strip():
            return None
        return _normalize_hhmm(v)

    @field_validator("estimated_tod_start", "estimated_tod_end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        return _normalize_hhmm(v)


class Victim(BaseModel):
    """Victim dossier and biological details."""
    name: str = Field(..., description="Full name of the victim.")
    age: int = Field(..., ge=1, le=120, description="Age of the victim.")
    occupation: str = Field(..., description="Occupation/Social standing of the victim.")
    forensic_data: ForensicData = Field(..., description="Forensic autopsy notes and measurements.")
    gender: Optional[str] = Field(default="Nam", description="Gender of the victim.")
    residence: Optional[str] = Field(default=None, description="Primary residence of the victim.")


class Suspect(BaseModel):
    """Suspect profile, motive, alibi, and guilt flag."""
    id: str = Field(..., description="Unique suspect identifier (e.g., 'SUSP-01').")
    name: str = Field(..., description="Full name of the suspect.")
    age: int = Field(..., ge=1, le=120, description="Age of the suspect.")
    occupation: str = Field(..., description="Occupation or relationship with the victim.")
    motive: str = Field(..., description="Motive or underlying conflict with the victim.")
    alibi_start: str = Field(..., description="Start time of claimed alibi (HH:MM).")
    alibi_end: str = Field(..., description="End time of claimed alibi (HH:MM).")
    alibi_statement: str = Field(..., description="Verbal alibi testimony given by the suspect.")
    secret_innocent_fact: Optional[str] = Field(default=None, description="Innocent secret creating a red-herring conflict.")
    is_culprit: bool = Field(default=False, description="Secret flag indicating if this suspect is the actual killer.")
    image_url: Optional[str] = Field(default=None, description="Static or on-demand URL of the portrait photograph.")
    gender: Optional[str] = Field(default="Nam", description="Gender of the suspect.")
    relationship_to_victim: Optional[str] = Field(default=None, description="Relationship with victim.")
    residence: Optional[str] = Field(default=None, description="Residence address or room location.")
    statement: Optional[str] = Field(default=None, description="Full verbatim formal interrogation statement.")
    timeline_claimed: Optional[str] = Field(default=None, description="Claimed movement timeline string.")
    interview_notes: Optional[str] = Field(default=None, description="Confidential interrogation notes by detective.")

    @field_validator("alibi_start", "alibi_end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format '{v}'. Expected 'HH:MM'.")
        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(f"Time '{v}' out of range (00:00 - 23:59).")
        return f"{hours:02d}:{minutes:02d}"


class Evidence(BaseModel):
    """Physical or documentary evidence found at the crime scene."""
    id: str = Field(..., description="Unique evidence identifier (e.g., 'EV-01').")
    title: str = Field(..., description="Short descriptive name of the evidence.")
    location: str = Field(..., description="Location where the evidence was discovered.")
    description: str = Field(..., description="Detailed description and forensic traits of the item.")
    linked_suspect_id: Optional[str] = Field(default=None, description="Optional ID of suspect linked to this item.")
    is_crucial: bool = Field(default=False, description="Whether this evidence is a key clue to break the case.")
    is_red_herring: bool = Field(default=False, description="Whether this clue is intentionally deceptive pointing to an innocent suspect.")
    image_url: Optional[str] = Field(default=None, description="Static or on-demand URL of the physical evidence photograph.")
    is_weapon: Optional[bool] = Field(default=False, description="Whether this evidence is the murder weapon.")
    fingerprint_analysis: Optional[str] = Field(default=None, description="Latent fingerprint forensic analysis report.")
    blood_dna_analysis: Optional[str] = Field(default=None, description="Serological and DNA forensic analysis report.")
    physical_condition: Optional[str] = Field(default=None, description="Detailed physical condition and mechanical traits.")



class GroundTruth(BaseModel):
    """Secret ground truth of the crime for validation and grading."""
    culprit_id: str = Field(..., description="ID of the true killer (must match a Suspect.id).")
    actual_crime_time: str = Field(..., description="Actual time when the murder was committed (HH:MM).")
    murder_weapon: str = Field(..., description="Actual weapon/mechanism used in the murder.")
    core_contradiction: str = Field(..., description="The decisive indirect contradiction that exposes the culprit.")

    @field_validator("actual_crime_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format '{v}'. Expected 'HH:MM'.")
        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(f"Time '{v}' out of range (00:00 - 23:59).")
        return f"{hours:02d}:{minutes:02d}"


# -------------------------------------------------------------
# Paper 3 Extensions: Multi-hop Deductive Reasoning Chain
# -------------------------------------------------------------

class DeductionStep(BaseModel):
    """A single hop in the multi-hop reasoning chain (from Paper 3 QaAgent)."""
    step_number: int = Field(..., description="Order of the deductive step (1, 2, ...).")
    clue_ids: List[str] = Field(..., description="List of evidence IDs involved in this reasoning step.")
    inference: str = Field(..., description="Logical deduction made by connecting these clues.")
    target_suspect_id: Optional[str] = Field(default=None, description="Suspect implicated or exonerated in this step.")


class ReasoningChain(BaseModel):
    """Complete multi-hop reasoning chain proving solvability of the case."""
    steps: List[DeductionStep] = Field(default_factory=list, description="Ordered steps of deduction.")
    final_conclusion: str = Field(..., description="Synthesis of the proof identifying the culprit.")
    decisive_contradiction: str = Field(..., description="The decisive contradiction that breaks the culprit's alibi.")


# -------------------------------------------------------------
# Paper 7 Extensions: Neuro-Symbolic Diagnostics & Repair Signals
# -------------------------------------------------------------

class ViolationType(str, Enum):
    """Categories of constraint violations for localized patch repair."""
    TOD_PHYSICS = "tod_physics"
    ALIBI_UNBROKEN = "alibi_unbroken"
    CRIME_TIME_OUTSIDE_TOD = "crime_time_outside_tod"
    NO_CRUCIAL_CLUE = "no_crucial_clue"
    DUPLICATE_ID = "duplicate_id"
    MULTIPLE_CULPRITS = "multiple_culprits"
    SCHEMA_ERROR = "schema_error"


class ConstraintViolation(BaseModel):
    """Detailed diagnostic violation signal for targeted localized repair."""
    violation_type: ViolationType
    component: str = Field(..., description="'outline', 'character', 'clue', or 'reasoning'")
    message: str = Field(..., description="Human and LLM-readable diagnostic description of the flaw.")
    target_id: Optional[str] = Field(default=None, description="ID of the suspect or evidence causing the violation.")


class ValidationResult(BaseModel):
    """Structured report returned by the Neuro-Symbolic Validator Engine."""
    is_valid: bool
    violations: List[ConstraintViolation] = Field(default_factory=list)
    diagnostic_feedback: str = Field(default="", description="Consolidated feedback for agent repair.")


class GenerationMetadata(BaseModel):
    """Operational telemetry and benchmark metrics for the generated case."""
    model_config = {"protected_namespaces": ()}
    model_name: str = Field(default="unknown")
    pipeline_version: str = Field(default="2.0-neuro-symbolic")
    config_mode: str = Field(default="full_pipeline", description="Ablation configuration mode.")
    agent_latencies: Dict[str, float] = Field(default_factory=dict, description="Latency per agent in seconds.")
    agent_models: Dict[str, str] = Field(
        default_factory=dict,
        description="Actual LLM model used per agent (including fallback)."
    )
    fallback_triggered: bool = Field(
        default=False,
        description="Whether any agent fell back to a secondary/smaller model."
    )
    used_fallback_sample: bool = Field(
        default=False,
        description="Whether offline seed sample case was used due to catastrophic generation failure."
    )
    token_usage: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed real token telemetry (prompt_tokens, completion_tokens, total_tokens, patch_tokens)."
    )
    total_latency: float = Field(default=0.0, description="Total generation time in seconds.")
    patch_retries: int = Field(default=0, description="Count of localized patch repairs performed.")
    validator_score: float = Field(default=1.0, description="Logic pass score (1.0 = clean, 0.0 = invalid).")


# -------------------------------------------------------------
# Case Dossier and API Payloads
# -------------------------------------------------------------

class DeductionVerdict(str, Enum):
    """Categorical evaluation verdict of the player's deduction."""
    SOLVED_PERFECT = "solved_perfect"              # Right killer + decisive clues + zero red herrings (100 pts)
    SOLVED_FLAWED = "solved_flawed"                # Right killer + decisive clues, but fell for minor distraction (60-80 pts)
    WRONG_SUSPECT = "wrong_suspect"                # Accused an innocent person (0 pts)
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"# Right killer, but failed to provide alibi-breaking evidence (35 pts)
    TRAPPED_BY_RED_HERRING = "trapped_by_red_herring" # Accused innocent or submitted decisive red herring trap (10-25 pts)
    SPAM_DETECTED = "spam_detected"                # Selected all or bulk random clues without deduction (0 pts)


class DeductionScoreBreakdown(BaseModel):
    """Detailed score telemetry for academic evaluation and UI display."""
    base_culprit_score: float = Field(default=0.0, description="Score for correctly identifying the killer (up to 40).")
    crucial_clues_score: float = Field(default=0.0, description="Score for crucial alibi-breaking evidence (up to 40).")
    precision_bonus: float = Field(default=0.0, description="Bonus for concise deduction without irrelevant clutter (up to 20).")
    red_herring_penalty: float = Field(default=0.0, description="Penalty for falling for misleading red-herrings.")
    total_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Final composite score (0 - 100).")


class ClientSuspect(BaseModel):
    """Sanitized suspect profile sent to game clients (no ground-truth cheat flags)."""
    id: str = Field(..., description="Unique suspect identifier (e.g., 'SUSP-01').")
    name: str = Field(..., description="Full name of the suspect.")
    age: int = Field(..., ge=1, le=120, description="Age of the suspect.")
    occupation: str = Field(..., description="Occupation or relationship with the victim.")
    motive: str = Field(..., description="Motive or underlying conflict with the victim.")
    alibi_start: str = Field(..., description="Start time of claimed alibi (HH:MM).")
    alibi_end: str = Field(..., description="End time of claimed alibi (HH:MM).")
    alibi_statement: str = Field(..., description="Verbal alibi testimony given by the suspect.")
    image_url: Optional[str] = Field(default=None, description="Static or on-demand URL of the portrait photograph.")
    gender: Optional[str] = Field(default="Nam", description="Gender of the suspect.")
    relationship_to_victim: Optional[str] = Field(default=None, description="Relationship with victim.")
    residence: Optional[str] = Field(default=None, description="Residence address or room location.")
    statement: Optional[str] = Field(default=None, description="Full verbatim formal interrogation statement.")
    timeline_claimed: Optional[str] = Field(default=None, description="Claimed movement timeline string.")
    interview_notes: Optional[str] = Field(default=None, description="Confidential interrogation notes by detective.")


class ClientEvidence(BaseModel):
    """Sanitized evidence item sent to game clients (no crucial/red-herring labels)."""
    id: str = Field(..., description="Unique evidence identifier (e.g., 'EV-01').")
    title: str = Field(..., description="Short descriptive name of the evidence.")
    location: str = Field(..., description="Location where the evidence was discovered.")
    description: str = Field(..., description="Detailed description and forensic traits of the item.")
    image_url: Optional[str] = Field(default=None, description="Static or on-demand URL of the physical evidence photograph.")
    is_weapon: Optional[bool] = Field(default=False, description="Whether this evidence is the murder weapon.")
    fingerprint_analysis: Optional[str] = Field(default=None, description="Latent fingerprint forensic analysis report.")
    blood_dna_analysis: Optional[str] = Field(default=None, description="Serological and DNA forensic analysis report.")
    physical_condition: Optional[str] = Field(default=None, description="Detailed physical condition and mechanical traits.")


class ClientCaseDossier(BaseModel):
    """Public case dossier for player-facing endpoints without solutions or cheat flags."""
    case_id: str = Field(..., description="Unique case code (e.g., 'CASE-2026-001').")
    title: str = Field(..., description="Title of the murder case.")
    summary: str = Field(..., description="Introduction and context of the locked-room mystery.")
    victim: Victim = Field(..., description="Victim profile and autopsy findings.")
    suspects: List[ClientSuspect] = Field(..., min_length=2, max_length=5, description="List of suspects.")
    evidences: List[ClientEvidence] = Field(..., min_length=2, description="List of physical evidences.")
    metadata: Optional[GenerationMetadata] = Field(default=None, description="Telemetry metadata.")


class CaseDossier(BaseModel):
    """Complete Case Dossier structure stored internally in database and used by solver."""
    case_id: str = Field(..., description="Unique case code (e.g., 'CASE-2026-001').")
    title: str = Field(..., description="Title of the murder case.")
    summary: str = Field(..., description="Introduction and context of the locked-room mystery.")
    victim: Victim = Field(..., description="Victim profile and autopsy findings.")
    suspects: List[Suspect] = Field(..., min_length=2, max_length=5, description="List of suspects.")
    evidences: List[Evidence] = Field(..., min_length=2, description="List of physical evidences.")
    ground_truth: GroundTruth = Field(..., description="Secret solution data.")
    reasoning_chain: Optional[ReasoningChain] = Field(default=None, description="Multi-hop deduction chain from Paper 3.")
    metadata: Optional[GenerationMetadata] = Field(default=None, description="Diagnostic telemetry and metrics.")

    def to_client_dossier(self) -> ClientCaseDossier:
        """Strip secret ground truth and internal flags before sending to client."""
        client_suspects = [
            ClientSuspect(
                id=s.id,
                name=s.name,
                age=s.age,
                occupation=s.occupation,
                motive=s.motive,
                alibi_start=s.alibi_start,
                alibi_end=s.alibi_end,
                alibi_statement=s.alibi_statement,
                image_url=s.image_url,
                gender=s.gender,
                relationship_to_victim=s.relationship_to_victim,
                residence=s.residence,
                statement=s.statement,
                timeline_claimed=s.timeline_claimed,
                interview_notes=s.interview_notes
            )
            for s in self.suspects
        ]
        client_evidences = [
            ClientEvidence(
                id=e.id,
                title=e.title,
                location=e.location,
                description=e.description,
                image_url=e.image_url,
                is_weapon=e.is_weapon,
                fingerprint_analysis=e.fingerprint_analysis,
                blood_dna_analysis=e.blood_dna_analysis,
                physical_condition=e.physical_condition
            )
            for e in self.evidences
        ]
        return ClientCaseDossier(
            case_id=self.case_id,
            title=self.title,
            summary=self.summary,
            victim=self.victim,
            suspects=client_suspects,
            evidences=client_evidences,
            metadata=self.metadata
        )


class VerifyRequest(BaseModel):
    """Request payload from player submitting their deduction."""
    case_id: str = Field(..., description="The ID of the case being solved.")
    selected_suspect_id: str = Field(..., description="The ID of the suspect accused by the player.")
    selected_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidences submitted as proof.")
    reasoning: Optional[str] = Field(default=None, description="Optional free-text deductive reasoning from player.")


class VerifyResponse(BaseModel):
    """Response payload detailing the player's deduction accuracy with granular scoring."""
    case_id: str
    is_correct: bool = Field(..., description="Overall verdict (True if culprit and crucial clues match).")
    verdict: DeductionVerdict = Field(default=DeductionVerdict.WRONG_SUSPECT, description="Categorical evaluation status.")
    culprit_identified: bool = Field(..., description="Whether the player correctly named the killer.")
    crucial_evidences_identified: bool = Field(..., description="Whether required key evidences were provided.")
    found_crucial_count: int = Field(default=0)
    total_crucial_count: int = Field(default=0)
    red_herrings_selected_count: int = Field(default=0)
    irrelevant_clues_count: int = Field(default=0)
    score: float = Field(default=0.0, description="Composite deduction score out of 100.")
    score_breakdown: Optional[DeductionScoreBreakdown] = Field(default=None)
    feedback: str = Field(..., description="Narrative evaluation / explanation for the player.")
    core_contradiction: Optional[str] = Field(default=None, description="Revealed explanation on victory.")
