from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///cd_organizer.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Funkcja init_db NIE MOŻE importować niczego z głównego modułu aplikacji
def init_db():
    Base.metadata.create_all(bind=engine)
