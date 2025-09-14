# backend/app/enhanced_utils.py
import os
import json
import math
import random
from typing import Optional, Dict, List, Any
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import logging

logger = logging.getLogger(__name__)

def extract_enhanced_metadata(image: Image.Image, image_bytes: bytes, gps_data: Dict, heading: Optional[float]) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from image and user data
    """
    metadata = {
        "gps": gps_data,
        "heading": heading,
        "image_info": {
            "size": image.size,
            "mode": image.mode,
            "format": image.format
        },
        "visual_features": extract_visual_features(image),
        "exif_gps": None
    }
    
    # Try to extract EXIF GPS as backup/validation
    try:
        exif_dict = piexif.load(image_bytes)
        gps_ifd = exif_dict.get("GPS", {})
        if gps_ifd:
            metadata["exif_gps"] = parse_gps_from_exif(gps_ifd)
    except Exception as e:
        logger.warning(f"Could not extract EXIF GPS: {e}")
    
    return metadata

def extract_visual_features(image: Image.Image) -> Dict[str, Any]:
    """
    Extract basic visual features that can help with matching
    In production, use computer vision APIs or custom models
    """
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Basic color analysis
    colors = image.getcolors(maxcolors=256*256*256)
    dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5] if colors else []
    
    # Image characteristics
    features = {
        "dominant_colors": [(count, color) for count, color in dominant_colors[:3]],
        "brightness": calculate_brightness(image),
        "contrast": calculate_contrast(image),
        "aspect_ratio": image.size[0] / image.size[1],
        "resolution": image.size[0] * image.size[1]
    }
    
    # TODO: Add actual landmark detection using:
    # - OpenAI Vision API
    # - Google Vision API  
    # - Custom trained model
    features["detected_landmarks"] = mock_landmark_detection(image)
    
    return features

def calculate_brightness(image: Image.Image) -> float:
    """Calculate average brightness of image"""
    grayscale = image.convert('L')
    histogram = grayscale.histogram()
    pixels = sum(histogram)
    brightness = sum(i * histogram[i] for i in range(256)) / pixels
    return brightness / 255.0

def calculate_contrast(image: Image.Image) -> float:
    """Calculate contrast of image"""
    grayscale = image.convert('L')
    histogram = grayscale.histogram()
    pixels = sum(histogram)
    mean = sum(i * histogram[i] for i in range(256)) / pixels
    variance = sum(((i - mean) ** 2) * histogram[i] for i in range(256)) / pixels
    return math.sqrt(variance) / 255.0

def mock_landmark_detection(image: Image.Image) -> List[str]:
    """
    Mock landmark detection - replace with real AI service
    """
    # In production, integrate with:
    # - OpenAI GPT-4 Vision
    # - Google Cloud Vision API
    # - AWS Rekognition
    # - Custom trained model
    
    chicago_landmarks = [
        "Chicago Theater", "Willis Tower", "Cloud Gate", "Navy Pier",
        "Wrigley Building", "Tribune Tower", "Art Institute",
        "Grant Park", "Millennium Park", "State Street"
    ]
    
    # Mock detection based on image characteristics
    detected = []
    if image.size[0] > 1000:  # High res might catch more detail
        detected.extend(random.sample(chicago_landmarks, min(2, len(chicago_landmarks))))
    
    return detected

def parse_gps_from_exif(gps_ifd: Dict) -> Optional[Dict[str, float]]:
    """Parse GPS coordinates from EXIF data"""
    try:
        def convert_to_degrees(value):
            d, m, s = value
            return d + (m / 60.0) + (s / 3600.0)
        
        lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
        lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
        lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude) 
        lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()
        
        if lat and lon:
            lat_deg = convert_to_degrees([x[0]/x[1] for x in lat])
            lon_deg = convert_to_degrees([x[0]/x[1] for x in lon])
            
            if lat_ref == 'S':
                lat_deg = -lat_deg
            if lon_ref == 'W':
                lon_deg = -lon_deg
                
            return {"latitude": lat_deg, "longitude": lon_deg}
    except Exception as e:
        logger.error(f"GPS parsing error: {e}")
    
    return None

def find_best_historical_match(metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Find the best historical photo match using multiple strategies
    """
    gps = metadata["gps"]
    heading = metadata.get("heading")
    visual_features = metadata.get("visual_features", {})
    
    # Load historical database (in production, use real database)
    historical_db = load_historical_database()
    
    # Strategy 1: Geographic proximity
    candidates = filter_by_proximity(historical_db, gps["latitude"], gps["longitude"], radius_km=0.5)
    
    if not candidates:
        return None
    
    # Strategy 2: Filter by viewing angle/heading
    if heading is not None:
        candidates = filter_by_heading(candidates, heading, tolerance_degrees=45)
    
    # Strategy 3: Visual similarity scoring
    scored_candidates = []
    for candidate in candidates:
        score = calculate_visual_similarity(visual_features, candidate.get("visual_features", {}))
        distance = calculate_distance(gps["latitude"], gps["longitude"], 
                                    candidate["gps"]["latitude"], candidate["gps"]["longitude"])
        
        # Combined score: visual similarity + proximity + era interest
        combined_score = (
            score * 0.4 +  # Visual similarity
            (1 - min(distance, 1)) * 0.3 +  # Proximity (closer = better)
            candidate.get("interest_score", 0.5) * 0.3  # Historical interest
        )
        
        candidate["match_score"] = combined_score
        candidate["distance_meters"] = distance * 1000
        scored_candidates.append(candidate)
    
    # Return best match
    if scored_candidates:
        best_match = max(scored_candidates, key=lambda x: x["match_score"])
        best_match["match_method"] = "multi_strategy"
        return best_match
    
    return None

def load_historical_database() -> List[Dict[str, Any]]:
    """
    Load historical photo database
    In production: PostgreSQL + PostGIS with proper indexing
    """
    # Mock database with Chicago locations
    return [
        {
            "url": "/historical/state_street_1950.jpg",
            "year": 1950,
            "gps": {"latitude": 41.8781, "longitude": -87.6278},
            "heading_range": [0, 90],  # North to East
            "landmarks": ["State Street", "Chicago Theater"],
            "interest_score": 0.9,
            "visual_features": {
                "dominant_colors": [(1000, (120, 100, 80))],
                "brightness": 0.6,
                "has_people": True,
                "has_cars": True,
                "architecture_style": "mid_century"
            }
        },
        {
            "url": "/historical/loop_1920.jpg", 
            "year": 1920,
            "gps": {"latitude": 41.8796, "longitude": -87.6237},
            "heading_range": [90, 180],  # East to South
            "landmarks": ["Loop District", "El Train"],
            "interest_score": 0.8,
            "visual_features": {
                "dominant_colors": [(800, (100, 90, 70))],
                "brightness": 0.4,
                "has_people": True,
                "has_cars": False,
                "architecture_style": "early_1900s"
            }
        },
        {
            "url": "/historical/michigan_ave_1960.jpg",
            "year": 1960, 
            "gps": {"latitude": 41.8819, "longitude": -87.6278},
            "heading_range": [270, 360],  # West to North
            "landmarks": ["Michigan Avenue", "Art Institute"],
            "interest_score": 0.85,
            "visual_features": {
                "dominant_colors": [(1200, (140, 120, 100))],
                "brightness": 0.7,
                "has_people": True,
                "has_cars": True,
                "architecture_style": "mid_century_modern"
            }
        }
    ]

def filter_by_proximity(database: List[Dict], lat: float, lon: float, radius_km: float = 0.5) -> List[Dict]:
    """Filter historical photos by geographic proximity"""
    candidates = []
    for item in database:
        distance = calculate_distance(lat, lon, item["gps"]["latitude"], item["gps"]["longitude"])
        if distance <= radius_km:
            candidates.append(item)
    return candidates

def filter_by_heading(candidates: List[Dict], user_heading: float, tolerance_degrees: int = 45) -> List[Dict]:
    """Filter by viewing direction/heading"""
    if user_heading is None:
        return candidates
    
    filtered = []
    for candidate in candidates:
        heading_range = candidate.get("heading_range", [0, 360])
        
        # Check if user heading falls within the photo's viewing range
        start, end = heading_range
        if start <= end:
            in_range = start <= user_heading <= end
        else:  # Range crosses 0 degrees (e.g., 350-30)
            in_range = user_heading >= start or user_heading <= end
            
        # Also check with tolerance
        if in_range or any(abs(user_heading - h) <= tolerance_degrees for h in heading_range):
            filtered.append(candidate)
    
    return filtered

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in kilometers"""
    R = 6371  # Earth's radius in km
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat/2) * math.sin(dlat/2) + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
         math.sin(dlon/2) * math.sin(dlon/2))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_visual_similarity(features1: Dict, features2: Dict) -> float:
    """Calculate visual similarity score between two images"""
    if not features1 or not features2:
        return 0.5  # Default similarity
    
    similarity_score = 0.5  # Base score
    
    # Compare brightness
    if "brightness" in features1 and "brightness" in features2:
        brightness_diff = abs(features1["brightness"] - features2["brightness"])
        similarity_score += (1 - brightness_diff) * 0.2
    
    # Compare dominant colors (simplified)
    if "dominant_colors" in features1 and "dominant_colors" in features2:
        # This is very simplified - in production use proper color space comparison
        similarity_score += 0.2  # Mock color similarity
    
    # Architectural era matching
    arch1 = features1.get("architecture_style", "")
    arch2 = features2.get("architecture_style", "")
    if arch1 == arch2 and arch1:
        similarity_score += 0.3
    
    return min(similarity_score, 1.0)

def calculate_confidence_score(metadata: Dict, match: Dict) -> int:
    """Calculate confidence percentage for the match"""
    base_confidence = 60
    
    # GPS accuracy bonus
    gps_accuracy = metadata["gps"].get("accuracy", 100)
    if gps_accuracy < 10:
        base_confidence += 20
    elif gps_accuracy < 50:
        base_confidence += 10
    
    # Distance penalty
    distance_km = match.get("distance_meters", 0) / 1000
    if distance_km < 0.1:
        base_confidence += 15
    elif distance_km < 0.3:
        base_confidence += 5
    else:
        base_confidence -= 10
    
    # Heading match bonus
    if metadata.get("heading") is not None:
        base_confidence += 10
    
    # Visual features bonus
    if metadata.get("visual_features", {}).get("detected_landmarks"):
        base_confidence += 15
    
    return min(max(base_confidence, 30), 95)

def generate_historical_story(match: Dict, metadata: Dict) -> Dict[str, str]:
    """Generate contextual story and facts for the historical match"""
    year = match.get("year", 1950)
    landmarks = match.get("landmarks", [])
    
    # In production, use AI to generate contextual stories
    # For now, use curated content based on location/era
    
    stories_db = {
        1920: {
            "quotes": [
                "The roar of the El train mixed with the clip-clop of horse-drawn carriages on State Street.",
                "Flappers and businessmen shared the sidewalks in the heart of America's Second City.",
                "The Chicago Loop buzzed with the energy of prohibition-era commerce."
            ],
            "facts": [
                "Chicago's elevated train system was already 30 years old by this time.",
                "The city was rebuilding rapidly after the Great Chicago Fire of 1871.",
                "State Street was known as 'That Great Street' and the shopping heart of the Midwest."
            ]
        },
        1950: {
            "quotes": [
                "Post-war optimism filled the air as Chicago modernized at breakneck speed.",
                "The sound of construction mixed with jazz spilling from nightclub doorways.",
                "Families flocked downtown
