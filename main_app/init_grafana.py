#!/usr/bin/env python3
from src.db.connection import (
    init_db_engine,
    init_db_model,
    get_db_engine,
    drop_db_model
)
from src.db.models import User
from sqlmodel import Session, select
from src.app_logic.grafana_user_operations import grafana_create_or_update_user
from src.app_logic.user_operations import get_all_users

def main() -> None:
    init_db_engine()
    session = Session(bind=get_db_engine())
    
    admin = session.scalar(select(User).where(User.username == 'admin'))
    grafana_create_or_update_user(
        user=admin,
        db_session=session,
        password='admin'
    )

    # TODO - load vars : . ./env_vars.sh
    # TODO - add email config for sending alerts
    # TODO - add prometheus to Grafana as datasource
    # TODO - change grafana docker folder permissions:
    #      $ chown 472:0 grafana-data/data
    # TODO - add function to get datasource from Grafana


if __name__ == '__main__':
    main()