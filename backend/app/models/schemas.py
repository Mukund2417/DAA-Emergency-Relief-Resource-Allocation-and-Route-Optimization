"""API boundary validation models."""
import math
from typing import Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class ScenarioIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scenario_type: str = Field(min_length=2, max_length=50)
    description: str = Field(default="", max_length=1000)
    status: str = Field(default="Planning", pattern="^(Planning|Active|Closed)$")


class LocationIn(BaseModel):
    scenario_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    identifier: str | None = Field(default=None, max_length=40)
    priority: int = Field(ge=1, le=5)
    latitude: float | None = Field(default=None, ge=-90, le=90,allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180,allow_inf_nan=False)
    x: float = Field(default=100, ge=0, le=5000,allow_inf_nan=False)
    y: float = Field(default=100, ge=0, le=5000,allow_inf_nan=False)
    demands: dict[str, float] = Field(default_factory=dict)

    @field_validator("demands")
    @classmethod
    def validate_demands(cls,value):
        if any(not math.isfinite(amount) or amount<0 for amount in value.values()):
            raise ValueError("Demand quantities must be finite and non-negative")
        return value


class ResourceIn(BaseModel):
    scenario_id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=40)
    unit: str = Field(min_length=1, max_length=24)
    available: float = Field(ge=0,allow_inf_nan=False)
    divisible: bool
    unit_weight: float = Field(gt=0,allow_inf_nan=False)
    value_score: float = Field(ge=0,allow_inf_nan=False)


class DemandIn(BaseModel):
    resource_type_id: int = Field(gt=0)
    quantity: float = Field(ge=0,allow_inf_nan=False)


class RoadNodeIn(BaseModel):
    scenario_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=100)
    location_id: int | None = Field(default=None, gt=0)
    x: float = Field(default=100, ge=0, le=5000)
    y: float = Field(default=100, ge=0, le=5000)


class RoadEdgeIn(BaseModel):
    scenario_id: int = Field(gt=0)
    source_id: int = Field(gt=0)
    target_id: int = Field(gt=0)
    distance: float = Field(ge=0,allow_inf_nan=False)
    blocked: bool = False


class AlgorithmInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    scenario_id: int | None = None
    input: dict[str, Any]


class BenchmarkInput(BaseModel):
    algorithm: str
    input_size: int = Field(ge=1, le=10000)
    repeats: int = Field(default=5, ge=1, le=100)
    seed: int = 42
