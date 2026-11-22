from fastapi import APIRouter

from app.api.routes import auth, dashboard, newsletters, tracking, users

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(newsletters.router)
api_router.include_router(tracking.router)
api_router.include_router(dashboard.router)


@api_router.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
