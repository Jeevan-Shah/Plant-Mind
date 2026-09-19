from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class PlantInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=120)
    species: str = Field(min_length=1, max_length=100)
    growth_stage: Literal['Seedling', 'Vegetative', 'Flowering', 'Fruiting', 'Mature', 'Dormant']
    age_days: int = Field(ge=0, le=36500)
    watering_frequency: str = Field(min_length=1, max_length=120)
    light_condition: str = Field(min_length=1, max_length=120)
    notes: str = Field(default='', max_length=4000)

class PlantOut(PlantInput):
    id: int
    created_at: datetime
    updated_at: datetime
    is_demo: bool
    health_status: str
    last_analysis: datetime | None
    latest_condition: str | None
    analysis_count: int
    image_path: str | None

class AnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plant_id: int
    plant_name: str
    image_path: str | None
    detected_symptoms: list[str]
    predicted_condition: str
    confidence: float
    plant_state: dict
    explanation: list[str]
    recommendation: list[dict]
    preventive_care: list[dict]
    evidence: dict
    limitations: list[str]
    model_status: str
    reasoning_mode: str
    llm_summary: str | None
    is_demo: bool
    created_at: datetime

class CareInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    event_type: Literal['Watering', 'Fertilizing', 'Pruning', 'Repotting', 'Observation']
    description: str = Field(min_length=1, max_length=2000)
    date: datetime | None = None

    @field_validator('date')
    @classmethod
    def timezone_required(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError('Include a timezone in the care event date')
        return value

class CareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plant_id: int
    event_type: str
    description: str
    date: datetime

class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    entity_type: str
    name: str
    description: str


class AnalysisRequest(BaseModel):
    symptoms: str | None = Field(default=None, max_length=2000)


class TripleOut(BaseModel):
    source: str
    source_name: str
    source_type: str
    relationship: str
    target: str
    target_name: str
    target_type: str


class RelationshipSetOut(BaseModel):
    entity: EntityOut | None
    outgoing: list[TripleOut]
    incoming: list[TripleOut]


class DashboardStats(BaseModel):
    total_plants: int
    total_analyses: int
    needs_attention: int
    healthy: int
    monitor: int
    new_plants: int
    status_breakdown: dict[str, int]
    recent_conditions: list[dict]


class HealthCheck(BaseModel):
    status: str
    version: str
    database: str
    graph_backend: str
    vision_model: str
    llm_configured: bool
    reasoning_mode: str
