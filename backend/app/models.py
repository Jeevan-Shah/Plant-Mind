from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now():
    return datetime.now(timezone.utc)

class Plant(Base):
    __tablename__ = 'plants'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    species: Mapped[str] = mapped_column(String(100))
    growth_stage: Mapped[str] = mapped_column(String(50))
    age_days: Mapped[int] = mapped_column(Integer)
    watering_frequency: Mapped[str] = mapped_column(String(120))
    light_condition: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str] = mapped_column(Text, default='')
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    analyses: Mapped[list['PlantAnalysis']] = relationship(back_populates='plant', cascade='all, delete-orphan', order_by='desc(PlantAnalysis.created_at)')
    care_events: Mapped[list['CareEvent']] = relationship(back_populates='plant', cascade='all, delete-orphan', order_by='desc(CareEvent.date)')

class PlantAnalysis(Base):
    __tablename__ = 'plant_analyses'
    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey('plants.id', ondelete='CASCADE'), index=True)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detected_symptoms: Mapped[list] = mapped_column(JSON)
    predicted_condition: Mapped[str] = mapped_column(String(150))
    confidence: Mapped[float] = mapped_column(Float)
    plant_state: Mapped[dict] = mapped_column(JSON)
    explanation: Mapped[list] = mapped_column(JSON)
    recommendation: Mapped[list] = mapped_column(JSON)
    preventive_care: Mapped[list] = mapped_column(JSON)
    evidence: Mapped[dict] = mapped_column(JSON)
    limitations: Mapped[list] = mapped_column(JSON)
    model_status: Mapped[str] = mapped_column(String(30), default='demo')
    reasoning_mode: Mapped[str] = mapped_column(String(80))
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    plant: Mapped[Plant] = relationship(back_populates='analyses')

class CareEvent(Base):
    __tablename__ = 'care_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    plant_id: Mapped[int] = mapped_column(ForeignKey('plants.id', ondelete='CASCADE'), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    plant: Mapped[Plant] = relationship(back_populates='care_events')

class KnowledgeEntity(Base):
    __tablename__ = 'knowledge_entities'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)

class KnowledgeRelationship(Base):
    __tablename__ = 'knowledge_relationships'
    id: Mapped[int] = mapped_column(primary_key=True)
    source_entity_id: Mapped[str] = mapped_column(ForeignKey('knowledge_entities.id'), index=True)
    relationship: Mapped[str] = mapped_column(String(80))
    target_entity_id: Mapped[str] = mapped_column(ForeignKey('knowledge_entities.id'), index=True)

class AppSetting(Base):
    __tablename__ = 'app_settings'
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))