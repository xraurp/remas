from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.db.connection import init_db_engine
#from src.app_logic.authentication import init_auth
from src.app_logic.scheduled_event_processing import (
    init_scheduler,
    shutdown_scheduler
)
from src.routes import (
    user_route,
    group_route,
    node_route,
    resource_route,
    resource_alias_route,
    task_route,
    task_tag_route,
    limit_route,
    notification_route,
    authentication_route
)
from src.config import get_settings
import logging

if get_settings().debug:
    rh = logging.getLogger('root')
    rh.setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    init_db_engine()
    #init_auth()
    init_scheduler()

    yield
    
    # Cleanup tasks
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    """
    Root endpoint for getting the ping.
    """
    return {"detail": "Hello World"}

@app.get('/grafana-link')
async def get_grafana_link():
    """
    Endpoint for getting the link to Grafana.
    """
    link = get_settings().grafana_redirect_url
    return {
        'detail': link
    }

app.include_router(user_route)
app.include_router(group_route)
app.include_router(node_route)
app.include_router(resource_route)
app.include_router(resource_alias_route)
app.include_router(task_route)
app.include_router(task_tag_route)
app.include_router(limit_route)
app.include_router(notification_route)
app.include_router(authentication_route)
