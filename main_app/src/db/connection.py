from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import Engine
from src.config import Settings


# Global object to store database engine
DB_ENGINE: Engine = None

def init_db_engine() -> None:
    """
    Initializes database engine and sessionmaker.
    """
    global DB_ENGINE
    DB_ENGINE = create_engine(
        url=Settings().database_url
        #,echo=True  # DEBUG
    )

def get_db_engine() -> Engine:
    """
    Engine getter.
    """
    global DB_ENGINE
    return DB_ENGINE

def get_db_session():
    """
    Creates session.
    """
    global DB_ENGINE
    with Session(bind=DB_ENGINE) as session:
        yield session

def init_db_model(engine: Engine) -> None:
    """
    Creates database and tables in the database
    :param engine: database engine to use
    """
    SQLModel.metadata.create_all(engine)

def drop_db_model(engine: Engine) -> None:
    """
    Drops/deletes database and tables in the database
    :param engine: database engine to use
    """
    SQLModel.metadata.drop_all(engine)
