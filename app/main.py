from fastapi import FastAPI

from app.api.routes.analytics import router as analytics_router
from app.api.routes.fire_events import router as fire_router
from app.api.routes.ingest import router as ingest_router
from app.db.base import Base
from app.db.session import engine
from app.models import fire_event

app = FastAPI(title="Wildfire API")

app.include_router(fire_router, tags=["Fire Events"])
app.include_router(ingest_router, tags=["Ingest"])
app.include_router(analytics_router, tags=["Analytics"])

Base.metadata.create_all(bind=engine)
