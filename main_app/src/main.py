from functools import lru_cache
from fastapi import FastAPI
from src.config import Settings
from contextlib import asynccontextmanager
from src.db.connection import init_db_engine
from src.routes import (
    user_route,
    group_route,
    node_route,
    resource_route,
    resource_alias_route,
    task_route,
    task_tag_route,
    limit_route,
    notification_route
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    init_db_engine()
    yield
    # Cleanup tasks


app = FastAPI(lifespan=lifespan)


@lru_cache
def get_settings():
    return Settings()

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(user_route)
app.include_router(group_route)
app.include_router(node_route)
app.include_router(resource_route)
app.include_router(resource_alias_route)
app.include_router(task_route)
app.include_router(task_tag_route)
app.include_router(limit_route)
app.include_router(notification_route)
