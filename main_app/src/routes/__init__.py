from sqlmodel import Session
from fastapi import Depends
from typing import Annotated

from src.db.connection import get_db_session


SessionDep = Annotated[Session, Depends(get_db_session)]

# import routes
from .user_routes import user_route
from .group_routes import group_route
from .node_routes import node_route
from .resource_routes import resource_route
from .resource_alias_routes import resource_alias_route
from .task_routes import task_route
from .task_tag_routes import task_tag_route
