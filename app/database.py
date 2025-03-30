from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
DATABASE_URL = 'sqlite:///cd_organizer.db'
engine = create_engine(DATABASE_URL)

def init_db():
    Base.metadata.create_all(engine)
