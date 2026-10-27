from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def get_health() -> dict[str, str]:
    """Liveness probe; it touches neither PostgreSQL nor Qdrant, so a dependency blip never reads as the API being down."""
    return {"status": "ok"}
