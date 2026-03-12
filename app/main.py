from fastapi import Depends, FastAPI

from app.api.deps import require_basic_auth
from app.api.routes.analytics import router as analytics_router
from app.api.routes.fire_events import router as fire_router
from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.db.base import Base
from app.db.session import engine
from app.models import disaster_event, ingest_run, source_metadata

app = FastAPI(title="Disaster Event Intelligence API")

app.include_router(
    fire_router,
    tags=["Events"],
    dependencies=[Depends(require_basic_auth)],
)
app.include_router(
    ingest_router,
    tags=["Ingest"],
    dependencies=[Depends(require_basic_auth)],
)
app.include_router(
    analytics_router,
    tags=["Analytics"],
    dependencies=[Depends(require_basic_auth)],
)
app.include_router(health_router, tags=["Health"])

Base.metadata.create_all(bind=engine)
