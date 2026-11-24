from typing import List, Optional
from datetime import datetime
from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Text, 
    Boolean, 
    ForeignKey, 
    DateTime, 
    func
)
from sqlalchemy.orm import relationship, Mapped
from app.core.database import Base

class Case(Base):
    """
    Bảng Vụ án (Case): Lưu thông tin tổng quan, trạng thái sinh vụ án và kết quả.
    Lưu ý: `culprit_id` cho phép nullable=True để giải quyết vấn đề khóa ngoại vòng (Circular Foreign Key)
    khi khởi tạo Case trước rồi mới UPDATE id hung thủ sau khi sinh danh sách Character.
    """
    __tablename__ = "cases"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    title: Mapped[str] = Column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = Column(Text, nullable=True)
    difficulty: Mapped[str] = Column(String(50), default="Medium", nullable=False)
    status: Mapped[str] = Column(
        String(50), 
        default="generating", 
        nullable=False,
        comment="Trạng thái: generating, ready, completed, failed"
    )
    
    # Báo cáo pháp y (Chỉ chứa dữ kiện hiện trường & sinh học tử thi, ẩn giờ chết)
    forensic_report: Mapped[Optional[str]] = Column(Text, nullable=True)
    
    # Khóa ngoại trỏ tới Character (Hung thủ) - nullable=True để tránh xung đột khởi tạo
    culprit_id: Mapped[Optional[int]] = Column(
        Integer, 
        ForeignKey("characters.id", use_alter=True, name="fk_case_culprit_id"), 
        nullable=True
    )
    
    created_at: Mapped[datetime] = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = Column(
        DateTime(timezone=True), 
        onupdate=func.now(), 
        nullable=True
    )

    # Relationships
    culprit: Mapped[Optional["Character"]] = relationship(
        "Character", 
        foreign_keys=[culprit_id], 
        post_update=True
    )
    characters: Mapped[List["Character"]] = relationship(
        "Character", 
        foreign_keys="Character.case_id", 
        back_populates="case", 
        cascade="all, delete-orphan"
    )
    timeline_events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", 
        back_populates="case", 
        cascade="all, delete-orphan"
    )
    evidences: Mapped[List["Evidence"]] = relationship(
        "Evidence", 
        back_populates="case", 
        cascade="all, delete-orphan"
    )


class Character(Base):
    """
    Bảng Nhân vật (Character): Nạn nhân (victim), Nghi phạm (suspect), Nhân chứng (witness).
    """
    __tablename__ = "characters"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("cases.id", ondelete="CASCADE"), 
        nullable=False
    )
    name: Mapped[str] = Column(String(100), nullable=False)
    age: Mapped[Optional[int]] = Column(Integer, nullable=True)
    role: Mapped[str] = Column(
        String(50), 
        nullable=False, 
        comment="Vai trò: victim, suspect, witness"
    )
    occupation: Mapped[Optional[str]] = Column(String(100), nullable=True)
    motive: Mapped[Optional[str]] = Column(Text, nullable=True, comment="Động cơ gây án")
    alibi: Mapped[Optional[str]] = Column(Text, nullable=True, comment="Chứng cứ ngoại phạm")
    persona: Mapped[Optional[str]] = Column(Text, nullable=True, comment="Tiểu sử và tính cách")
    is_culprit: Mapped[bool] = Column(Boolean, default=False, nullable=False)

    # Relationships
    case: Mapped["Case"] = relationship(
        "Case", 
        foreign_keys=[case_id], 
        back_populates="characters"
    )
    events: Mapped[List["TimelineEvent"]] = relationship(
        "TimelineEvent", 
        back_populates="character"
    )
    related_evidences: Mapped[List["Evidence"]] = relationship(
        "Evidence", 
        back_populates="related_character"
    )


class TimelineEvent(Base):
    """
    Bảng Sự kiện Dòng thời gian (TimelineEvent): Các mốc sự kiện diễn ra xung quanh vụ án.
    """
    __tablename__ = "timeline_events"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("cases.id", ondelete="CASCADE"), 
        nullable=False
    )
    event_time: Mapped[str] = Column(
        String(100), 
        nullable=False, 
        comment="Thời gian diễn ra (VD: 21:15 - 21:45)"
    )
    description: Mapped[str] = Column(Text, nullable=False)
    location: Mapped[Optional[str]] = Column(String(255), nullable=True)
    character_id: Mapped[Optional[int]] = Column(
        Integer, 
        ForeignKey("characters.id", ondelete="SET NULL"), 
        nullable=True
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="timeline_events")
    character: Mapped[Optional["Character"]] = relationship("Character", back_populates="events")


class Evidence(Base):
    """
    Bảng Chứng cứ (Evidence): Chứng cứ vật lý, vết tích tại hiện trường hoặc vật dụng liên quan.
    """
    __tablename__ = "evidences"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    case_id: Mapped[int] = Column(
        Integer, 
        ForeignKey("cases.id", ondelete="CASCADE"), 
        nullable=False
    )
    item_name: Mapped[str] = Column(String(255), nullable=False)
    description: Mapped[str] = Column(Text, nullable=False)
    location_found: Mapped[Optional[str]] = Column(String(255), nullable=True)
    related_character_id: Mapped[Optional[int]] = Column(
        Integer, 
        ForeignKey("characters.id", ondelete="SET NULL"), 
        nullable=True
    )
    is_key_evidence: Mapped[bool] = Column(
        Boolean, 
        default=False, 
        nullable=False, 
        comment="Chứng cứ mấu chốt để phá án"
    )

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="evidences")
    related_character: Mapped[Optional["Character"]] = relationship(
        "Character", 
        back_populates="related_evidences"
    )
