from fastapi import FastAPI
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
app.include_router(authentication_route)
