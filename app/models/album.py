from sqlalchemy import Column, Integer, String
from app.database import Base

class Album(Base):
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    year = Column(Integer)
    discogs_id = Column(Integer, unique=True)  # Nowe pole
