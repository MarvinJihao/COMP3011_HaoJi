from fastapi import FastAPI
from app.api.routes.fire_events import router as fire_events_router

app = FastAPI()

app.include_router(fire_events_router)