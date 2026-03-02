from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.security import get_current_user

from .schemas import *
from .service import AIIntelligenceService

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


@router.get("/demand-planning", response_model=DemandPlanningResponse)
def get_demand_planning(
    vendor_id: int = Query(..., description="Vendor ID to analyze"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> DemandPlanningResponse:
    """Get AI-powered demand planning insights"""
    service = AIIntelligenceService(db)
    return service.get_demand_planning(vendor_id)


@router.get("/capacity-recommendation", response_model=CapacityRecommendationResponse)
def get_capacity_recommendation(
    vendor_id: int = Query(..., description="Vendor ID for capacity analysis"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> CapacityRecommendationResponse:
    """Get AI capacity recommendation for vendor"""
    service = AIIntelligenceService(db)
    return service.get_capacity_recommendation(vendor_id)


@router.get("/slot-recommendations", response_model=SlotRecommendationsResponse)
def get_slot_recommendations(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> SlotRecommendationsResponse:
    """Get AI-powered smart slot recommendations"""
    service = AIIntelligenceService(db)
    return service.get_slot_recommendations(user["id"] if user else None)


@router.get("/predictive-eta", response_model=PredictiveETAResponse)
def get_predictive_eta(
    slot_id: int = Query(..., description="Slot ID to predict ETA for"),
    vendor_id: int = Query(..., description="Vendor ID for ETA calculation"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> PredictiveETAResponse:
    """Get AI predictive ETA and pickup window"""
    service = AIIntelligenceService(db)
    return service.get_predictive_eta(slot_id, vendor_id)


@router.get("/vendor-ranking", response_model=VendorRankingResponse)
def get_vendor_ranking(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> VendorRankingResponse:
    """Get AI-powered vendor rankings and load analytics"""
    service = AIIntelligenceService(db)
    return service.get_vendor_ranking()


@router.get("/personalization", response_model=PersonalizationResponse)
def get_personalization(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> PersonalizationResponse:
    """Get personalized recommendations and suggestions"""
    service = AIIntelligenceService(db)
    return service.get_personalization(user["id"])


@router.get("/reorder-suggestions", response_model=ReorderSuggestionsResponse)
def get_reorder_suggestions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ReorderSuggestionsResponse:
    """Get AI-powered smart reorder suggestions"""
    service = AIIntelligenceService(db)
    return service.get_reorder_suggestions(user["id"])


@router.get("/proactive-alerts", response_model=ProactiveAlertsResponse)
def get_proactive_alerts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> ProactiveAlertsResponse:
    """Get AI-driven proactive alerts and warnings"""
    service = AIIntelligenceService(db)
    return service.get_proactive_alerts(user["id"])


@router.get("/group-coordination", response_model=GroupCoordinationResponse)
def get_group_coordination(
    user_ids: list[int] = Query(..., description="List of user IDs for coordination"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> GroupCoordinationResponse:
    """Get AI-powered group coordination intelligence"""
    service = AIIntelligenceService(db)
    return service.get_group_coordination(user_ids)


@router.get("/signals")
def get_user_signals(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    service = AIIntelligenceService(db)
    return {"signals": service.get_user_signals(user["id"])}


@router.get("/signals/rush-hour")
def get_rush_hour_signals(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    service = AIIntelligenceService(db)
    return {"signals": service.get_rush_hour_signals(user["id"])}


@router.get("/signals/slot-suggestions")
def get_slot_suggestion_signals(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    service = AIIntelligenceService(db)
    return {"signals": service.get_slot_suggestion_signals(user["id"])}


@router.get("/signals/reorder-prompts")
def get_reorder_prompt_signals(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
) -> dict[str, Any]:
    service = AIIntelligenceService(db)
    return {"signals": service.get_reorder_prompt_signals(user["id"])}
