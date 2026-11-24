"""Database Persistence Layer for AI Detective Game Engine.

Provides SQLite persistence using SQLAlchemy 2.0:
- CaseRecord: Stores procedural and curated case dossiers with indexed metadata.
- DeductionRecord: Logs player/agent deduction trials for telemetry and grading analysis.
- BenchmarkRunRecord: Stores multi-model benchmark evaluation results for thesis Chapter 4.
- Automatic migration from legacy JSON files in cases/ to SQLite on startup.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Generator

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    DateTime,
    ForeignKey,
    select,
    func,
    desc,
    event,
    cast
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session,
    relationship,
    Mapped,
    mapped_column
)

from models import CaseDossier, VerifyRequest, VerifyResponse, DeductionVerdict

logger = logging.getLogger("detective-db")

# Database Path Configuration
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_DIR, "detective.db")
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Engine with SQLite multithreading support for FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SQLITE_BUSY_TIMEOUT_MS = 5000


@event.listens_for(Engine, "connect")
def _configure_sqlite(dbapi_connection, connection_record):
    """Enable FK enforcement, WAL journaling and a busy timeout on every SQLite connection.

    - foreign_keys: SQLite ignores FOREIGN KEY / ON DELETE CASCADE unless enabled per connection.
    - WAL: readers no longer block the writer, so several LAN players can verify/log at once.
    - busy_timeout: wait instead of failing immediately with "database is locked".
    """
    if type(dbapi_connection).__module__.split(".")[0] != "sqlite3":
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ---------------------------------------------------------------------------
# SQLAlchemy ORM Models
# ---------------------------------------------------------------------------

class CaseRecord(Base):
    """Persistent storage for full Case Dossiers and indexed searchable metadata."""
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    era: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mystery_type: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    culprit_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    actual_crime_time: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    validator_score: Mapped[float] = mapped_column(Float, default=1.0)
    suspects_count: Mapped[int] = mapped_column(Integer, default=0)
    evidences_count: Mapped[int] = mapped_column(Integer, default=0)
    dossier_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to player deduction logs
    deductions = relationship("DeductionRecord", back_populates="case", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata summary to dictionary for list views."""
        return {
            "case_id": self.case_id,
            "title": self.title,
            "summary": self.summary,
            "country": self.country,
            "era": self.era,
            "mystery_type": self.mystery_type,
            "culprit_id": self.culprit_id,
            "actual_crime_time": self.actual_crime_time,
            "is_valid": self.is_valid,
            "validator_score": self.validator_score,
            "suspects_count": self.suspects_count,
            "evidences_count": self.evidences_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class DeductionRecord(Base):
    """Audit log of player/agent deductions and verdict scores."""
    __tablename__ = "deduction_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("cases.case_id", ondelete="CASCADE"), index=True, nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    accused_id: Mapped[str] = mapped_column(String(32), nullable=False)
    selected_evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    is_correct: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False)
    verdict: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    culprit_identified: Mapped[bool] = mapped_column(Boolean, default=False)
    crucial_evidences_identified: Mapped[bool] = mapped_column(Boolean, default=False)
    found_crucial_count: Mapped[int] = mapped_column(Integer, default=0)
    total_crucial_count: Mapped[int] = mapped_column(Integer, default=0)
    red_herrings_selected_count: Mapped[int] = mapped_column(Integer, default=0)
    irrelevant_clues_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    case = relationship("CaseRecord", back_populates="deductions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert deduction log to dictionary."""
        return {
            "id": self.id,
            "case_id": self.case_id,
            "session_id": self.session_id,
            "accused_id": self.accused_id,
            "selected_evidence_ids": json.loads(self.selected_evidence_ids_json or "[]"),
            "is_correct": self.is_correct,
            "verdict": self.verdict,
            "culprit_identified": self.culprit_identified,
            "crucial_evidences_identified": self.crucial_evidences_identified,
            "found_crucial_count": self.found_crucial_count,
            "total_crucial_count": self.total_crucial_count,
            "red_herrings_selected_count": self.red_herrings_selected_count,
            "irrelevant_clues_count": self.irrelevant_clues_count,
            "score": self.score,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class BenchmarkRunRecord(Base):
    """Academic benchmark results for comparing LLM models across trials."""
    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    trial_index: Mapped[int] = mapped_column(Integer, nullable=False)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    schema_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    logic_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    repair_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    violation_types_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Database Session Dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CRUD & Repository Operations
# ---------------------------------------------------------------------------

KNOWN_COUNTRIES = ["Việt Nam", "Nhật Bản", "Anh Quốc"]
KNOWN_MYSTERY_TYPES = [
    "Án mạng phòng kín",
    "Biệt thự cô lập",
    "Tranh chấp tài sản",
    "Án mạng thương trường"
]


def _guess_from_text(text: str, candidates: List[str]) -> Optional[str]:
    """Fallback for legacy cases that were stored without explicit metadata."""
    lowered = text.lower()
    return next((c for c in candidates if c.lower() in lowered), None)


def save_case_to_db(
    case: CaseDossier,
    db: Optional[Session] = None,
    is_valid: Optional[bool] = None,
    validator_score: Optional[float] = None,
    country: Optional[str] = None,
    era: Optional[str] = None,
    mystery_type: Optional[str] = None
) -> CaseRecord:
    """Save or update a CaseDossier into SQLite.

    country / era / mystery_type should come from the generation request; when absent
    (legacy JSON migration), they are guessed from the title and summary.
    is_valid and validator_score default to case.metadata telemetry if present.
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

    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        record = db.execute(select(CaseRecord).where(CaseRecord.case_id == case.case_id)).scalar_one_or_none()
        
        full_text = f"{case.title} {case.summary}"
        country = country or _guess_from_text(full_text, KNOWN_COUNTRIES)
        mystery_type = mystery_type or _guess_from_text(full_text, KNOWN_MYSTERY_TYPES)

        # Compact JSON: the DB copy is machine-read only (pretty files live in cases/).
        dossier_json_str = case.model_dump_json()

        if record is None:
            record = CaseRecord(
                case_id=case.case_id,
                title=case.title,
                summary=case.summary,
                country=country,
                era=era,
                mystery_type=mystery_type,
                culprit_id=case.ground_truth.culprit_id,
                actual_crime_time=case.ground_truth.actual_crime_time,
                is_valid=is_valid,
                validator_score=validator_score,
                suspects_count=len(case.suspects),
                evidences_count=len(case.evidences),
                dossier_json=dossier_json_str,
                created_at=datetime.now(timezone.utc)
            )
            db.add(record)
        else:
            record.title = case.title
            record.summary = case.summary
            if country:
                record.country = country
            if era:
                record.era = era
            if mystery_type:
                record.mystery_type = mystery_type
            record.culprit_id = case.ground_truth.culprit_id
            record.actual_crime_time = case.ground_truth.actual_crime_time
            record.is_valid = is_valid
            record.validator_score = validator_score
            record.suspects_count = len(case.suspects)
            record.evidences_count = len(case.evidences)
            record.dossier_json = dossier_json_str
            record.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(record)
        logger.info(f"Successfully persisted Case '{case.case_id}' to SQLite database.")
        return record
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist case '{case.case_id}' to SQLite: {e}")
        raise e
    finally:
        if own_session:
            db.close()


def get_case_from_db(case_id: str, db: Optional[Session] = None) -> Optional[CaseDossier]:
    """Retrieve and deserialize a CaseDossier from SQLite by case_id."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        record = db.execute(select(CaseRecord).where(CaseRecord.case_id == case_id)).scalar_one_or_none()
        if not record:
            return None
        return CaseDossier.model_validate_json(record.dossier_json)
    except Exception as e:
        logger.error(f"Error fetching case '{case_id}' from DB: {e}")
        return None
    finally:
        if own_session:
            db.close()


def _apply_case_filters(query, country: Optional[str], mystery_type: Optional[str], is_valid_only: bool):
    if country:
        query = query.where(CaseRecord.country == country)
    if mystery_type:
        query = query.where(CaseRecord.mystery_type == mystery_type)
    if is_valid_only:
        query = query.where(CaseRecord.is_valid.is_(True))
    return query


def list_cases_from_db(
    db: Optional[Session] = None,
    skip: int = 0,
    limit: Optional[int] = 50,
    country: Optional[str] = None,
    mystery_type: Optional[str] = None,
    is_valid_only: bool = False
) -> List[Dict[str, Any]]:
    """List case summaries with optional filtering. limit=None returns every match."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        query = _apply_case_filters(select(CaseRecord), country, mystery_type, is_valid_only)
        query = query.order_by(desc(CaseRecord.created_at)).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        results = db.execute(query).scalars().all()
        return [r.to_dict() for r in results]
    finally:
        if own_session:
            db.close()


def count_cases_in_db(
    db: Optional[Session] = None,
    country: Optional[str] = None,
    mystery_type: Optional[str] = None,
    is_valid_only: bool = False
) -> int:
    """Total number of cases matching the filters (for pagination metadata)."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        query = _apply_case_filters(select(func.count(CaseRecord.id)), country, mystery_type, is_valid_only)
        return int(db.execute(query).scalar_one())
    finally:
        if own_session:
            db.close()


def log_deduction_to_db(
    case_id: str,
    verify_req: VerifyRequest,
    verify_res: VerifyResponse,
    db: Optional[Session] = None,
    session_id: Optional[str] = None
) -> DeductionRecord:
    """Log player deduction attempt and result to SQLite for academic analytics."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        record = DeductionRecord(
            case_id=case_id,
            session_id=session_id,
            accused_id=verify_req.selected_suspect_id,
            selected_evidence_ids_json=json.dumps(verify_req.selected_evidence_ids),
            is_correct=verify_res.is_correct,
            verdict=verify_res.verdict.value if hasattr(verify_res.verdict, "value") else str(verify_res.verdict),
            culprit_identified=verify_res.culprit_identified,
            crucial_evidences_identified=verify_res.crucial_evidences_identified,
            found_crucial_count=verify_res.found_crucial_count,
            total_crucial_count=verify_res.total_crucial_count,
            red_herrings_selected_count=verify_res.red_herrings_selected_count,
            irrelevant_clues_count=verify_res.irrelevant_clues_count,
            score=verify_res.score,
            feedback=verify_res.feedback,
            created_at=datetime.now(timezone.utc)
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Logged deduction for case '{case_id}': verdict={record.verdict}, score={record.score}")
        return record
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log deduction for case '{case_id}': {e}")
        raise e
    finally:
        if own_session:
            db.close()


def get_case_statistics(case_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Compute player solve rates and error statistics for a given case."""
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        by_case = DeductionRecord.case_id == case_id
        total, solved, avg_score = db.execute(
            select(
                func.count(DeductionRecord.id),
                func.coalesce(func.sum(cast(DeductionRecord.is_correct, Integer)), 0),
                func.coalesce(func.avg(DeductionRecord.score), 0.0)
            ).where(by_case)
        ).one()

        if total == 0:
            return {
                "case_id": case_id,
                "total_attempts": 0,
                "solved_count": 0,
                "solve_rate_percentage": 0.0,
                "average_score": 0.0,
                "common_verdicts": {},
                "accused_frequency": {}
            }

        verdict_counts = dict(db.execute(
            select(DeductionRecord.verdict, func.count()).where(by_case).group_by(DeductionRecord.verdict)
        ).all())
        accused_counts = dict(db.execute(
            select(DeductionRecord.accused_id, func.count()).where(by_case).group_by(DeductionRecord.accused_id)
        ).all())

        return {
            "case_id": case_id,
            "total_attempts": total,
            "solved_count": solved,
            "solve_rate_percentage": round((solved / total) * 100.0, 2),
            "average_score": round(float(avg_score), 2),
            "common_verdicts": verdict_counts,
            "accused_frequency": accused_counts
        }
    finally:
        if own_session:
            db.close()


# ---------------------------------------------------------------------------
# Database Initialization & Auto-Migration from JSON Files
# ---------------------------------------------------------------------------

def init_db(seed_cases_dir: Optional[str] = None):
    """Create tables and automatically migrate existing JSON cases from disk into SQLite."""
    logger.info(f"Initializing SQLite database at: {DB_FILE}")
    Base.metadata.create_all(bind=engine)

    if seed_cases_dir is None:
        seed_cases_dir = os.path.join(DB_DIR, "cases")

    if not os.path.exists(seed_cases_dir):
        logger.warning(f"Cases directory not found: {seed_cases_dir}")
        return

    migrated_count = 0
    benchmark_migrated = 0
    with SessionLocal() as db:
        for fname in os.listdir(seed_cases_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(seed_cases_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    case = CaseDossier.model_validate(data)
                    
                    # Check if already in database
                    existing = db.execute(select(CaseRecord).where(CaseRecord.case_id == case.case_id)).scalar_one_or_none()
                    if not existing:
                        save_case_to_db(case, db=db, is_valid=True, validator_score=1.0)
                        migrated_count += 1
                except Exception as e:
                    logger.warning(f"Could not migrate legacy case '{fname}': {e}")

        # Populate benchmark_runs from benchmark_results.json if empty
        existing_runs = db.execute(select(func.count(BenchmarkRunRecord.id))).scalar_one()
        benchmark_json_path = os.path.join(DB_DIR, "benchmark_results.json")
        if existing_runs == 0 and os.path.exists(benchmark_json_path):
            try:
                with open(benchmark_json_path, "r", encoding="utf-8") as f:
                    runs_data = json.load(f)
                for idx, item in enumerate(runs_data, start=1):
                    record = BenchmarkRunRecord(
                        run_id="benchmark_30_trials_v1",
                        model_name=str(item.get("model", "unknown")),
                        trial_index=int(item.get("trial", idx)),
                        case_id=item.get("case_id"),
                        schema_valid=bool(item.get("json_valid", True)),
                        logic_valid=bool(item.get("logic_valid", True)),
                        repair_applied=bool(int(item.get("patch_retries", 0)) > 0),
                        latency_seconds=float(item.get("latency_sec", 0.0)),
                        violation_types_json=json.dumps(item.get("violation_types", []), ensure_ascii=False),
                    )
                    db.add(record)
                    benchmark_migrated += 1
                db.commit()
            except Exception as e:
                db.rollback()
                logger.warning(f"Could not migrate benchmark_results.json: {e}")

    logger.info(
        f"Database initialization complete. Migrated {migrated_count} cases and {benchmark_migrated} benchmark runs from disk."
    )


if __name__ == "__main__":
    init_db()
