"""Pydantic v2 Data Models and Schemas for AI Detective Game Engine.

Defines strictly typed structures for Victims, Suspects, Evidences,
Forensic Data, Ground Truth, Multi-hop Reasoning Chains (Paper 3),
Neuro-Symbolic Constraint Diagnostics (Paper 7), Case Dossiers, and API payloads.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ForensicData(BaseModel):
    """Forensic biological data and post-mortem findings."""
    ambient_temp: float = Field(..., description="Ambient temperature of the crime scene in Celsius (°C).")
    body_temp: float = Field(..., description="Body core temperature upon discovery in Celsius (°C).")
    livor_mortis_state: str = Field(..., description="State of livor mortis (e.g., 'Hoen ố cố định ở lưng', 'Blanchable on pressure').")
    wound_description: str = Field(..., description="Detailed description of fatal and non-fatal wounds.")
    estimated_tod_start: str = Field(..., description="Estimated start time of death (HH:MM, 24-hour format).")
    estimated_tod_end: str = Field(..., description="Estimated end time of death (HH:MM, 24-hour format).")

    @field_validator("estimated_tod_start", "estimated_tod_end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        parts = v.strip().split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time format '{v}'. Expected 'HH:MM'.")
        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(f"Time '{v}' out of range (00:00 - 23:59).")
        return f"{hours:02d}:{minutes:02d}"


class Victim(BaseModel):
    """Victim dossier and biological details."""
    name: str = Field(..., description="Full name of the victim.")
    age: int = Field(..., ge=1, le=120, description="Age of the victim.")
    occupation: str = Field(..., description="Occupation/Social standing of the victim.")
    forensic_data: ForensicData = Field(..., description="Forensic autopsy notes and measurements.")


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
    model_name: str = Field(default="unknown")
    pipeline_version: str = Field(default="2.0-neuro-symbolic")
    agent_latencies: Dict[str, float] = Field(default_factory=dict, description="Latency per agent in seconds.")
    total_latency: float = Field(default=0.0, description="Total generation time in seconds.")
    patch_retries: int = Field(default=0, description="Count of localized patch repairs performed.")
    validator_score: float = Field(default=1.0, description="Logic pass score (1.0 = clean, 0.0 = invalid).")


# -------------------------------------------------------------
# Case Dossier and API Payloads
# -------------------------------------------------------------

class CaseDossier(BaseModel):
    """Complete Case Dossier structure returned to client and stored in database."""
    case_id: str = Field(..., description="Unique case code (e.g., 'CASE-2026-001').")
    title: str = Field(..., description="Title of the murder case.")
    summary: str = Field(..., description="Introduction and context of the locked-room mystery.")
    victim: Victim = Field(..., description="Victim profile and autopsy findings.")
    suspects: List[Suspect] = Field(..., min_length=2, max_length=5, description="List of suspects.")
    evidences: List[Evidence] = Field(..., min_length=2, description="List of physical evidences.")
    ground_truth: GroundTruth = Field(..., description="Secret solution data.")
    reasoning_chain: Optional[ReasoningChain] = Field(default=None, description="Multi-hop deduction chain from Paper 3.")
    metadata: Optional[GenerationMetadata] = Field(default=None, description="Diagnostic telemetry and metrics.")


class VerifyRequest(BaseModel):
    """Request payload from player submitting their deduction."""
    case_id: str = Field(..., description="The ID of the case being solved.")
    selected_suspect_id: str = Field(..., description="The ID of the suspect accused by the player.")
    selected_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidences submitted as proof.")


class VerifyResponse(BaseModel):
    """Response payload detailing the player's deduction accuracy."""
    case_id: str
    is_correct: bool = Field(..., description="Overall verdict (True if culprit and crucial clues match).")
    culprit_identified: bool = Field(..., description="Whether the player correctly named the killer.")
    crucial_evidences_identified: bool = Field(..., description="Whether required key evidences were provided.")
    found_crucial_count: int
    total_crucial_count: int
    feedback: str = Field(..., description="Narrative evaluation / explanation for the player.")
    core_contradiction: Optional[str] = Field(default=None, description="Revealed explanation on victory.")
