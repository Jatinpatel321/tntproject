from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DemandPlanningResponse(BaseModel):
    expected_daily_orders: int
    slot_wise_demand_graph: Dict[str, int]
    popular_items: List[Dict[str, Any]]
    stationery_workload_score: float
    food_waste_risk_score: float


class CapacityRecommendationResponse(BaseModel):
    vendor_id: int
    recommended_capacity: int
    reasoning: str


class SlotRecommendation(BaseModel):
    slot_id: int
    score: float
    reasoning: str
    estimated_eta_minutes: int


class SlotRecommendationsResponse(BaseModel):
    recommendations: List[SlotRecommendation]
    best_slot_id: int


class PredictiveETAResponse(BaseModel):
    predicted_eta_minutes: int
    pickup_window_start: datetime
    pickup_window_end: datetime
    delay_risk_level: str  # LOW, MEDIUM, HIGH


class VendorRanking(BaseModel):
    vendor_id: int
    vendor_rank_score: float
    live_load_indicator: str  # LOW, MEDIUM, HIGH
    express_pickup_eligible: bool
    reasoning: str


class VendorRankingResponse(BaseModel):
    rankings: List[VendorRanking]


class PersonalizationResponse(BaseModel):
    recommended_for_you: List[Dict[str, Any]]
    smart_suggestions: List[Dict[str, Any]]
    active_preferences: Dict[str, Any] = {}


class ReorderSuggestion(BaseModel):
    item_id: int
    quantity: int
    slot_id: Optional[int]
    print_settings: Optional[Dict[str, Any]]


class ReorderSuggestionsResponse(BaseModel):
    suggestions: List[ReorderSuggestion]
    best_time_to_reorder: str


class AIAlert(BaseModel):
    type: str
    severity: str  # LOW, MEDIUM, HIGH
    explanation: str
    suggested_action: str


class ProactiveAlertsResponse(BaseModel):
    alerts: List[AIAlert]


class GroupCoordinationResponse(BaseModel):
    overlapping_windows: List[Dict[str, Any]]
    suggested_unified_slot: Optional[int]
    coordination_score: float
