from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import DbSession, StaffUser
from app.schemas.dashboard import DashboardStats
from app.services.stats import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(
    _: StaffUser,
    db: DbSession,
    days: Annotated[int, Query(ge=1, le=365, description="Daily traffic window")] = 30,
):
    return get_dashboard_stats(db, days)
