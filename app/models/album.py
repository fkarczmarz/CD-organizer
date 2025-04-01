from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Album(Base):
    __tablename__ = 'albums'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    artist = Column(String)
    year = Column(Integer)
    discogs_id = Column(Integer, unique=True)  # ID z Discogs
    cover_url = Column(Text)  # URL okładki
    genre = Column(String)  # Gatunek muzyczny
    country = Column(String)  # Kraj wydania
    format = Column(String)  # Format nośnika (np. CD, Vinyl)
