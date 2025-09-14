# backend/app/database.py
"""
Production database setup with PostGIS for spatial queries
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
from datetime import datetime

# Database URL - use PostGIS for spatial features
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost/streettimemachine"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HistoricalPhoto(Base):
    """
    Historical photo records with spatial indexing
    """
    __tablename__ = "historical_photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    title = Column(String)
    description = Column(Text)
    year = Column(Integer, nullable=False)
    decade = Column(Integer, nullable=False)  # For grouping: 1950, 1960, etc.
    
    # Spatial data - use PostGIS POINT
    location = Column(Geometry('POINT', srid=4326), nullable=False)
    
    # Photo metadata
    photographer = Column(String)
    source = Column(String)
    copyright_info = Column(String)
    
    # Visual features (stored as JSON or separate table)
    dominant_colors = Column(Text)  # JSON string
    brightness = Column(Float)
    contrast = Column(Float)
    has_people = Column(Boolean, default=False)
    has_vehicles = Column(Boolean, default=False)
    
    # Matching metadata
    viewing_direction_start = Column(Integer)  # 0-360 degrees
    viewing_direction_end = Column(Integer)    # 0-360 degrees
    landmarks = Column(Text)  # JSON array of landmark names
    street_address = Column(String)
    
    # Quality scores
    image_quality_score = Column(Float, default=0.5)  # 0-1
    historical_interest_score = Column(Float, default=0.5)  # 0-1
    match_popularity = Column(Integer, default=0)  # How often it's matched
    
    # Admin fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
class UserPhoto(Base):
    """
    User submitted photos and matches
    """
    __tablename__ = "user_photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String)  # Anonymous session tracking
    user_id = Column(String)  # If user is registered
    
    # Original photo metadata
    filename = Column(String)
    location = Column(Geometry('POINT', srid=4326))
    heading = Column(Integer)  # 0-360 degrees
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Match results
    matched_historical_photo_id = Column(UUID(as_uuid=True))
    confidence_score = Column(Integer)  # 0-100
    match_method = Column(String)  # "gps_proximity", "visual_similarity", etc.
    
    # User engagement
    user_shared = Column(Boolean, default=False)
    user_rating = Column(Integer)  # 1-5 stars
    
class MatchingLog(Base):
    """
    Log all matching attempts for analytics and improvement
    """
    __tablename__ = "matching_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_photo_id = Column(UUID(as_uuid=True))
    
    # Input data
    gps_accuracy = Column(Float)
    has_heading = Column(Boolean)
    visual_features_detected = Column(Text)  # JSON
    
    # Processing results
    candidates_found = Column(Integer)
    best_match_score = Column(Float)
    processing_time_ms = Column(Integer)
    
    # Outcomes
    match_found = Column(Boolean)
    user_satisfied = Column(Boolean)  # Based on user feedback
    
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database initialization
def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Spatial query helpers
def find_photos_near_location(db, latitude: float, longitude: float, radius_meters: int = 500):
    """
    Find historical photos within radius of location using PostGIS
    """
    # ST_DWithin uses meters when using geography type
    query = f"""
    SELECT *, 
           ST_Distance(location, ST_GeogFromText('POINT({longitude} {latitude})')) as distance_meters
    FROM historical_photos 
    WHERE ST_DWithin(
        location::geography, 
        ST_GeogFromText('POINT({longitude} {latitude})'), 
        {radius_meters}
    )
    AND is_active = true
    ORDER BY distance_meters
    """
    return db.execute(query).fetchall()

def find_photos_by_heading(db, latitude: float, longitude: float, heading: int, radius_meters: int = 500):
    """
    Find photos that match both location and viewing direction
    """
    query = f"""
    SELECT *, 
           ST_Distance(location, ST_GeogFromText('POINT({longitude} {latitude})')) as distance_meters
    FROM historical_photos 
    WHERE ST_DWithin(
        location::geography, 
        ST_GeogFromText('POINT({longitude} {latitude})'), 
        {radius_meters}
    )
    AND is_active = true
    AND (
        (viewing_direction_start <= viewing_direction_end 
         AND {heading} BETWEEN viewing_direction_start AND viewing_direction_end)
        OR 
        (viewing_direction_start > viewing_direction_end 
         AND ({heading} >= viewing_direction_start OR {heading} <= viewing_direction_end))
    )
    ORDER BY distance_meters, historical_interest_score DESC
    """
    return db.execute(query).fetchall()

# Sample data for testing
SAMPLE_HISTORICAL_DATA = [
    {
        "filename": "state_street_1950.jpg",
        "title": "State Street Looking North", 
        "year": 1950,
        "decade": 1950,
        "latitude": 41.8781,
        "longitude": -87.6278,
        "viewing_direction_start": 350,
        "viewing_direction_end": 10,
        "landmarks": '["Chicago Theater", "State Street"]',
        "street_address": "State Street, Chicago, IL",
        "image_quality_score": 0.9,
        "historical_interest_score": 0.85,
        "has_people": True,
        "has_vehicles": True
    },
    {
        "filename": "loop_1920.jpg",
        "title": "The Loop District",
        "year": 1920, 
        "decade": 1920,
        "latitude": 41.8796,
        "longitude": -87.6237,
        "viewing_direction_start": 80,
        "viewing_direction_end": 120,
        "landmarks": '["Loop District", "El Train"]',
        "street_address": "LaSalle Street, Chicago, IL",
        "image_quality_score": 0.7,
        "historical_interest_score": 0.9,
        "has_people": True,
        "has_vehicles": False
    }
]

def seed_database(db):
    """Insert sample historical photos"""
    for data in SAMPLE_HISTORICAL_DATA:
        photo = HistoricalPhoto(
            filename=data["filename"],
            title=data["title"],
            year=data["year"],
            decade=data["decade"],
            location=f"POINT({data['longitude']} {data['latitude']})",
            viewing_direction_start=data["viewing_direction_start"],
            viewing_direction_end=data["viewing_direction_end"],
            landmarks=data["landmarks"],
            street_address=data["street_address"],
            image_quality_score=data["image_quality_score"],
            historical_interest_score=data["historical_interest_score"],
            has_people=data["has_people"],
            has_vehicles=data["has_vehicles"]
        )
        db.add(photo)
    db.commit()
