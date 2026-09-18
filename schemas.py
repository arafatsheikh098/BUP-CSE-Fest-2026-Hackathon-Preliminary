from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# --- Request Schemas ---

class HourEntry(BaseModel):
    hour: int
    demand_kwh: float
    solar_kwh: float
    tariff_bdt_per_kwh: float

class BatterySpecs(BaseModel):
    capacity_kwh: float
    initial_energy_kwh: float
    minimum_energy_kwh: float
    max_charge_kwh_per_hour: float
    max_discharge_kwh_per_hour: float

class OptimizeEnergyRequest(BaseModel):
    scenario_id: str
    operator_notes: List[str]
    hours: List[HourEntry]
    battery: BatterySpecs

# --- Inner Structures for Directives ---

class StructuredAdjustment(BaseModel):
    hours: Optional[List[int]] = None
    factor: Optional[float] = None
    minimum_energy_kwh: Optional[float] = None
    max_grid_kwh: Optional[float] = None

# --- Response Schemas ---

class DirectiveInterpretationEntry(BaseModel):
    note_index: int
    applies: bool
    directive_type: str
    structured_adjustment: Optional[StructuredAdjustment] = None
    explanation: str

class HourlyPlanEntry(BaseModel):
    hour: int
    grid_kwh: float
    solar_used_kwh: float
    battery_action: str # "charge", "discharge", "idle"
    battery_kwh: float
    battery_energy_after_kwh: float

class OptimizeEnergyResponse(BaseModel):
    scenario_id: str
    directive_interpretation: List[DirectiveInterpretationEntry]
    hourly_plan: List[HourlyPlanEntry]
    total_grid_kwh: float
    total_cost_bdt: float
    peak_grid_kwh: float
    plan_summary: str

# --- Schema for LLM Output ---
# This is what we ask the LLM to return
class LLMDirective(BaseModel):
    directive_type: Literal[
        "solar_reduction", 
        "minimum_battery_reserve", 
        "no_charge_window", 
        "no_discharge_window", 
        "max_grid_window", 
        "no_op"
    ]
    hours: Optional[List[int]] = None
    factor: Optional[float] = None
    minimum_energy_kwh: Optional[float] = None
    max_grid_kwh: Optional[float] = None
    explanation: str

class LLMResponse(BaseModel):
    directives: List[LLMDirective]
