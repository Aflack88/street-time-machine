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

# Import our comprehensive data
from chicago_data import CHICAGO_HISTORICAL_PHOTOS, get_historical_story
from ai_vision import enhance_location_detection

logger = logging.getLogger(__name__)

def extract_enhanced_metadata(image: Image.Image, image_bytes: bytes, gps_data: Dict, heading: Optional[float]) -> Dict[str, Any]:
    """
    Extract comprehensive metadata using AI vision analysis
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
    
    # Enhanced location detection using AI
    try:
        enhanced_location = enhance_location_detection(
            image, 
            metadata["exif_gps"], 
            gps_data
        )
        metadata["enhanced_location"] = enhanced_location
        
        # Use the best available location
        if enhanced_location["final_location"]:
            metadata["best_location"] = enhanced_location["final_location"]
        else:
            metadata["best_location"] = gps_data
            
    except Exception as e:
        logger.error(f"Enhanced location detection failed: {e}")
        metadata["best_location"] = gps_data
    
    return metadata

def extract_visual_features(image: Image.Image) -> Dict[str, Any]:
    """
    Extract basic visual features for matching
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Basic color analysis
    colors = image.getcolors(maxcolors=256*256*256)
    dominant_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:5] if colors else []
    
    features = {
        "dominant_colors": [(count, color) for count, color in dominant_colors[:3]],
        "brightness": calculate_brightness(image),
        "contrast": calculate_contrast(image),
        "aspect_ratio": image.size[0] / image.size[1],
        "resolution": image.size[0] * image.size[1]
    }
    
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
    Find the best historical photo match using our comprehensive database
    """
    # Use the best available location
    location = metadata.get("best_location") or metadata.get("gps")
    if not location:
        logger.warning("No location data available for matching")
        return None
        
    lat = location["latitude"]
    lon = location["longitude"]
    heading = metadata.get("heading")
    
    logger.info(f"Searching for matches near {lat}, {lon}")
    
    # Load our comprehensive historical database
    historical_db = CHICAGO_HISTORICAL_PHOTOS
    
    # Strategy 1: Geographic proximity
    candidates = filter_by_proximity(historical_db, lat, lon, radius_km=1.0)  # Increased radius
    
    if not candidates:
        logger.warning(f"No candidates found within 1km of {lat}, {lon}")
        return None
    
    logger.info(f"Found {len(candidates)} candidates within 1km")
    
    # Strategy 2: Filter by viewing angle/heading
    if heading is not None:
        heading_filtered = filter_by_heading(candidates, heading, tolerance_degrees=60)
        if heading_filtered:
            candidates = heading_filtered
            logger.info(f"Filtered to {len(candidates)} candidates by heading")
    
    # Strategy 3: Enhanced scoring with AI analysis
    scored_candidates = []
    ai_analysis = metadata.get("enhanced_location", {}).get("ai_analysis", {})
    
    for candidate in candidates:
        # Distance scoring
        distance = calculate_distance(lat, lon, candidate["latitude"], candidate["longitude"])
        distance_score = max(0, 1 - (distance / 2.0))  # Normalize to 0-1
        
        # AI landmark matching
        ai_landmarks = ai_analysis.get("landmarks", [])
        candidate_landmarks = candidate.get("landmarks", [])
        landmark_matches = len(set(ai_landmarks) & set(candidate_landmarks))
        landmark_score = min(landmark_matches * 0.3, 1.0)
        
        # Historical interest score
        interest_score = candidate.get("historical_interest_score", 0.5)
        
        # Combine scores
        combined_score = (
            distance_score * 0.4 +  # Distance is important
            landmark_score * 0.3 +  # AI landmark matching
            interest_score * 0.3    # Historical significance
        )
        
        candidate_copy = candidate.copy()
        candidate_copy["match_score"] = combined_score
        candidate_copy["distance_meters"] = distance * 1000
        candidate_copy["landmark_matches"] = landmark_matches
        
        scored_candidates.append(candidate_copy)
    
    # Return best match
    if scored_candidates:
        best_match = max(scored_candidates, key=lambda x: x["match_score"])
        best_match["match_method"] = "comprehensive_ai_analysis"
        
        logger.info(f"Best match: {best_match['title']} ({best_match['year']}) with score {best_match['match_score']:.2f}")
        return best_match
    
    return None

def filter_by_proximity(database: List[Dict], lat: float, lon: float, radius_km: float = 1.0) -> List[Dict]:
    """Filter historical photos by geographic proximity"""
    candidates = []
    for item in database:
        distance = calculate_distance(lat, lon, item["latitude"], item["longitude"])
        if distance <= radius_km:
            candidates.append(item)
    return candidates

def filter_by_heading(candidates: List[Dict], user_heading: float, tolerance_degrees: int = 60) -> List[Dict]:
    """Filter by viewing direction/heading"""
    if user_heading is None:
        return candidates
    
    filtered = []
    for candidate in candidates:
        start = candidate.get("viewing_direction_start", 0)
        end = candidate.get("viewing_direction_end", 360)
        
        # Check if user heading falls within the photo's viewing range
        if start <= end:
            in_range = start <= user_heading <= end
        else:  # Range crosses 0 degrees (e.g., 350-30)
            in_range = user_heading >= start or user_heading <= end
            
        # Also check with tolerance
        if in_range or any(abs(user_heading - h) <= tolerance_degrees for h in [start, end]):
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

def calculate_confidence_score(metadata: Dict, match: Dict) -> int:
    """Calculate confidence percentage for the match"""
    base_confidence = 50
    
    # Enhanced location analysis confidence
    enhanced_location = metadata.get("enhanced_location", {})
    location_confidence = enhanced_location.get("confidence_score", 0.3)
    base_confidence += int(location_confidence * 30)
    
    # AI analysis boosts
    ai_analysis = enhanced_location.get("ai_analysis", {})
    if ai_analysis.get("chicago_likelihood", 0) > 0.7:
        base_confidence += 15
    
    if ai_analysis.get("landmarks"):
        base_confidence += 10
    
    # Distance penalty/bonus
    distance_km = match.get("distance_meters", 0) / 1000
    if distance_km < 0.2:
        base_confidence += 20
    elif distance_km < 0.5:
        base_confidence += 10
    elif distance_km > 1.5:
        base_confidence -= 15
    
    # Landmark matches bonus
    if match.get("landmark_matches", 0) > 0:
        base_confidence += match["landmark_matches"] * 5
    
    # Heading match bonus
    if metadata.get("heading") is not None:
        base_confidence += 8
    
    # Match score bonus
    match_score = match.get("match_score", 0.5)
    base_confidence += int(match_score * 20)
    
    return min(max(base_confidence, 20), 95)

def generate_historical_story(match: Dict, metadata: Dict) -> Dict[str, str]:
    """Generate contextual story using our comprehensive database"""
    year = match.get("year", 1950)
    landmarks = match.get("landmarks", [])
    
    # Use our comprehensive story database
    story = get_historical_story(year, landmarks)
    
    # Add specific context from the match
    if match.get("story_context"):
        story["context"] = match["story_context"]
    
    # Add AI analysis insights
    ai_analysis = metadata.get("enhanced_location", {}).get("ai_analysis", {})
    if ai_analysis.get("ai_raw_analysis"):
        story["ai_insights"] = f"AI Analysis: {ai_analysis['ai_raw_analysis'][:200]}..."
    
    return story
