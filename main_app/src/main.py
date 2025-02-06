from functools import lru_cache
from fastapi import FastAPI
from .config import Settings

app = FastAPI()

@lru_cache
def get_settings():
    return Settings()

@app.get("/")
async def root():
    return {"message": "Hello World"}
