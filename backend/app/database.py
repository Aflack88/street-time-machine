# backend/app/database.py
"""
Updated database schema with auto-curation support
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
import uuid
from datetime import datetime

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./street_time_machine.db"  # SQLite for development
)

# For production with PostGIS:
# DATABASE_URL = "postgresql://user:password@localhost/streettimemachine"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class HistoricalPhoto(Base):
    """
    Enhanced historical photo records with auto-curation support
    """
    __tablename__ = "historical_photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False, unique=True)
    title = Column(String)
    description = Column(Text)
    year = Column(Integer, nullable=False)
    decade = Column(Integer, nullable=False)
    
    # Location data (use TEXT for SQLite compatibility)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_accuracy = Column(Integer, default=100)  # meters
    location_source = Column(String)  # "gps", "landmark", "ai_inference"
    
    # Photo metadata
    photographer = Column(String)
    source = Column(String)  # "Library of Congress", "Flickr", etc.
    source_url = Column(String)  # Original URL
    copyright_info = Column(String)
    
    # Visual features (JSON strings for SQLite compatibility)
    landmarks = Column(Text)  # JSON array of landmark names
    dominant_colors = Column(Text)  # JSON string
    brightness = Column(Float)
    contrast = Column(Float)
    has_people = Column(Boolean, default=False)
    has_vehicles = Column(Boolean, default=False)
    architecture_style = Column(String)
    
    # Viewing direction
    viewing_direction_start = Column(Integer)  # 0-360 degrees
    viewing_direction_end = Column(Integer)    # 0-360 degrees
    street_address = Column(String)
    neighborhood = Column(String)
    
    # Quality and interest scores
    image_quality_score = Column(Float, default=0.5)
    historical_interest_score = Column(Float, default=0.5)
    match_popularity = Column(Integer, default=0)  # How often matched
    user_rating_avg = Column(Float, default=0.0)
    user_rating_count = Column(Integer, default=0)
    
    # Auto-curation fields
    auto_curated = Column(Boolean, default=False)
    ai_analysis_data = Column(Text)  # JSON of AI analysis
    curation_date = Column(DateTime)
    approved_by_ai = Column(Boolean, default=False)
    manual_review_needed = Column(Boolean, default=False)
    
    # Admin fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class CurationLog(Base):
    """
    Track auto-curation activities
    """
    __tablename__ = "curation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_date = Column(DateTime, default=datetime.utcnow)
    
    # Cycle statistics
    photos_discovered = Column(Integer, default=0)
    photos_processed = Column(Integer, default=0)
    photos_approved = Column(Integer, default=0)
    photos_stored = Column(Integer, default=0)
    
    # Performance metrics
    duration_seconds = Column(Float)
    success_rate = Column(Float)
    
    # Source breakdown
    library_of_congress_count = Column(Integer, default=0)
    flickr_count = Column(Integer, default=0)
    wikimedia_count = Column(Integer, default=0)
    unsplash_count = Column(Integer, default=0)
    
    # Quality metrics
    avg_chicago_relevance = Column(Float)
    avg_image_quality = Column(Float)
    avg_historical_value = Column(Float)
    
    # Errors and issues
    error_count = Column(Integer, default=0)
    error_details = Column(Text)  # JSON of error messages

class UserPhotoMatch(Base):
    """
    Track user photo matches for continuous improvement
    """
    __tablename__ = "user_photo_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String)
    user_id = Column(String)
    
    # User photo data
    user_photo_filename = Column(String)
    user_latitude = Column(Float)
    user_longitude = Column(Float)
    user_heading = Column(Integer)
    
    # Match results
    matched_photo_id = Column(UUID(as_uuid=True))
    confidence_score = Column(Integer)
    distance_meters = Column(Float)
    
    # User feedback
    user_satisfied = Column(Boolean)
    user_rating = Column(Integer)  # 1-5 stars
    user_shared = Column(Boolean, default=False)
    
    # AI analysis of user photo
    user_photo_ai_analysis = Column(Text)  # JSON
    
    # Improvement opportunities
    needs_better_match = Column(Boolean, default=False)
    suggested_improvements = Column(Text)  # JSON
    
    timestamp = Column(DateTime, default=datetime.utcnow)

class PhotoQualityFeedback(Base):
    """
    Collect feedback to improve AI curation quality
    """
    __tablename__ = "photo_quality_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    photo_id = Column(UUID(as_uuid=True))
    
    # Feedback data
    feedback_type = Column(String)  # "quality", "relevance", "accuracy"
    rating = Column(Integer)  # 1-5 scale
    comments = Column(Text)
    reporter_type = Column(String)  # "user", "admin", "ai_review"
    
    # Context
    match_context = Column(Text)  # What search led to this photo
    improvement_suggestions = Column(Text)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

# Database utilities
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

# Helper functions for SQLite spatial queries (simplified)
def find_photos_near_location(db, latitude: float, longitude: float, radius_km: float = 0.5):
    """
    Find historical photos within radius using simple distance calculation
    """
    import math
    
    # Simple bounding box calculation for SQLite
    lat_delta = radius_km / 111.0  # Rough conversion: 1 degree ≈ 111 km
    lon_delta = radius_km / (111.0 * math.cos(math.radians(latitude)))
    
    min_lat = latitude - lat_delta
    max_lat = latitude + lat_delta
    min_lon = longitude - lon_delta
    max_lon = longitude + lon_delta
    
    photos = db.query(HistoricalPhoto).filter(
        HistoricalPhoto.latitude.between(min_lat, max_lat),
        HistoricalPhoto.longitude.between(min_lon, max_lon),
        HistoricalPhoto.is_active == True
    ).all()
    
    # Calculate actual distances and filter
    nearby_photos = []
    for photo in photos:
        distance = calculate_distance(latitude, longitude, photo.latitude, photo.longitude)
        if distance <= radius_km:
            # Add distance as attribute for sorting
            photo.distance_km = distance
            nearby_photos.append(photo)
    
    # Sort by distance
    return sorted(nearby_photos, key=lambda p: p.distance_km)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers"""
    import math
    
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Initialize database with sample data
def seed_initial_data(db):
    """
    Add some initial Chicago photos for testing
    """
    from chicago_data import CHICAGO_HISTORICAL_PHOTOS
    import json
    
    for photo_data in CHICAGO_HISTORICAL_PHOTOS[:5]:  # Just add a few for testing
        try:
            existing = db.query(HistoricalPhoto).filter(
                HistoricalPhoto.filename == photo_data["filename"]
            ).first()
            
            if not existing:
                photo = HistoricalPhoto(
                    filename=photo_data["filename"],
                    title=photo_data["title"],
                    description=photo_data.get("description", ""),
                    year=photo_data["year"],
                    decade=photo_data["decade"],
                    latitude=photo_data["latitude"],
                    longitude=photo_data["longitude"],
                    location_accuracy=200,
                    location_source="manual_entry",
                    source=photo_data.get("source", "Chicago Archives"),
                    landmarks=json.dumps(photo_data.get("landmarks", [])),
                    viewing_direction_start=photo_data.get("viewing_direction_start", 0),
                    viewing_direction_end=photo_data.get("viewing_direction_end", 360),
                    street_address=photo_data.get("street_address", ""),
                    image_quality_score=photo_data.get("image_quality_score", 0.8),
                    historical_interest_score=photo_data.get("historical_interest_score", 0.8),
                    has_people=photo_data.get("has_people", False),
                    has_vehicles=photo_data.get("has_vehicles", False),
                    architecture_style=photo_data.get("architecture_style", ""),
                    auto_curated=False,
                    approved_by_ai=True
                )
                db.add(photo)
        
        except Exception as e:
            print(f"Error seeding photo {photo_data['filename']}: {e}")
            continue
    
    try:
        db.commit()
        print("Database seeded with initial Chicago photos")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()

if __name__ == "__main__":
    # Create tables and seed data
    create_tables()
    db = SessionLocal()
    seed_initial_data(db)
    db.close()
    print("Database setup complete!")
