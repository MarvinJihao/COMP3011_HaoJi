from fastapi import APIRouter

router = APIRouter(prefix="/fire-events", tags=["fire-events"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/")
def list_fire_events():
    # TODO: replace with real data from DB later
    return {"events": []}