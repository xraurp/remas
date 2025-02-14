from functools import lru_cache
from fastapi import FastAPI
from src.config import Settings
from contextlib import asynccontextmanager
from src.db.connection import init_db_engine
from src.routes import user_route, group_route

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
