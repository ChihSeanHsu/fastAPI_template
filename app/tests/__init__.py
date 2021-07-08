from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:example@db/postgres"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)
