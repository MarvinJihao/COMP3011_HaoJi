from fastapi import FastAPI
from app.api.routes.fire_events import router as fire_router
from app.db.session import engine
from app.db.base import Base
from app.models import fire_event  # 重要：确保模型被 import

app = FastAPI()

# 注册路由
app.include_router(fire_router, tags=["Fire Events"])

Base.metadata.create_all(bind=engine)

