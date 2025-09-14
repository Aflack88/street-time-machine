# backend/app/ai_vision.py
"""
OpenAI Vision API integration for photo analysis
"""
import os
import base64
import io
from typing import Dict, List, Optional
import openai
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

def encode_image_to_base64(image: Image.Image) -> str:
    """Convert PIL image to base64 string for OpenAI API"""
    # Resize image if too large (OpenAI has size limits)
    if image.size[0] > 1024 or image.size[1] > 1024:
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Save to bytes
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()
    
    # Encode to base64
    return base64.b64encode(img_bytes).decode('utf-8')

def analyze_photo_with_ai(image: Image.Image, user_location: Optional[Dict] = None) -> Dict:
    """
    Use OpenAI Vision to analyze the photo and extract location/landmark information
    """
    if not openai.api_key:
        logger.warning("OpenAI API key not configured - using fallback analysis")
        return fallback_analysis(image)
    
    try:
        # Encode image
        base64_image = encode_image_to_base64(image)
        
        # Create the prompt
        location_hint = ""
        if user_location:
            location_hint = f" The photo was taken near coordinates {user_location.get('latitude')}, {user_location.get('longitude')}."
        
        prompt = f"""Analyze this photo and help identify the location. Please provide:

1. **Location Analysis**: What city/area does this appear to be? Look for architectural styles, street signs, landmarks, or other identifying features.

2. **Landmarks**: What specific buildings, monuments, or notable structures can you see?

3. **Street Features**: Describe the street layout, intersections, or distinctive urban features.

4. **Time Period Clues**: Based on architecture, vehicles, clothing, or other visible elements, what time period might this represent?

5. **Geographic Clues**: Any signs, license plates, or other text that might indicate location?

6. **Chicago-Specific**: Does anything in this photo suggest it could be Chicago? Look for:
   - Elevated train tracks or stations
   - Chicago-style architecture (brick buildings, fire escapes)
   - Lake Michigan or Chicago River
   - Recognizable Chicago landmarks
   - Chicago street grid system

{location_hint}

Format your response as a JSON-like structure with clear categories. Be specific about what you can see versus what you're inferring."""

        # Call OpenAI Vision API
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        ai_analysis = response.choices[0].message.content
        
        # Parse the AI response into structured data
        parsed_analysis = parse_ai_analysis(ai_analysis)
        
        logger.info(f"OpenAI Vision analysis completed: {len(ai_analysis)} characters")
        return parsed_analysis
        
    except Exception as e:
        logger.error(f"OpenAI Vision analysis failed: {e}")
        return fallback_analysis(image)

def parse_ai_analysis(ai_text: str) -> Dict:
    """
    Parse the AI analysis text into structured data
    """
    # This is a simplified parser - in production, you might want more sophisticated parsing
    analysis = {
        "landmarks": [],
        "location_confidence": 0.5,
        "chicago_likelihood": 0.5,
        "architectural_era": "unknown",
        "street_features": [],
        "ai_raw_analysis": ai_text,
        "detected_text": [],
        "geographic_clues": []
    }
    
    text_lower = ai_text.lower()
    
    # Look for Chicago-specific mentions
    chicago_keywords = [
        "chicago", "loop", "magnificent mile", "lake michigan", 
        "chi-town", "windy city", "el train", "elevated", "wrigley",
        "sears tower", "willis tower", "navy pier", "millennium park",
        "grant park", "lincoln park", "gold coast", "river north"
    ]
    
    chicago_mentions = sum(1 for keyword in chicago_keywords if keyword in text_lower)
    analysis["chicago_likelihood"] = min(0.9, 0.3 + (chicago_mentions * 0.15))
    
    # Extract landmarks mentioned in the text
    chicago_landmarks = [
        "Chicago Theater", "Willis Tower", "Sears Tower", "Navy Pier", 
        "Millennium Park", "Grant Park", "Wrigley Field", "Union Station",
        "Art Institute", "Lincoln Park Zoo", "Buckingham Fountain",
        "Chicago Riverwalk", "Magnificent Mile", "State Street"
    ]
    
    for landmark in chicago_landmarks:
        if landmark.lower() in text_lower:
            analysis["landmarks"].append(landmark)
    
    # Detect architectural era mentions
    era_keywords = {
        "victorian": 1890,
        "art deco": 1930, 
        "mid-century": 1950,
        "modern": 1970,
        "contemporary": 1990,
        "brutalist": 1970,
        "prairie school": 1910,
        "chicago school": 1890
    }
    
    for era_name, year in era_keywords.items():
        if era_name in text_lower:
            analysis["architectural_era"] = era_name
            analysis["estimated_era_year"] = year
            break
    
    # Set confidence based on specificity
    if analysis["landmarks"] or "chicago" in text_lower:
        analysis["location_confidence"] = min(0.9, 0.6 + len(analysis["landmarks"]) * 0.1)
    
    return analysis

def fallback_analysis(image: Image.Image) -> Dict:
    """
    Fallback analysis when OpenAI Vision is not available
    """
    return {
        "landmarks": [],
        "location_confidence": 0.3,
        "chicago_likelihood": 0.5,
        "architectural_era": "unknown",
        "street_features": [],
        "ai_raw_analysis": "OpenAI Vision not available - using basic image analysis",
        "detected_text": [],
        "geographic_clues": [],
        "fallback_mode": True
    }

def enhance_location_detection(image: Image.Image, exif_gps: Optional[Dict], user_gps: Optional[Dict]) -> Dict:
    """
    Combine AI analysis with GPS data to improve location detection
    """
    # Get AI analysis
    ai_analysis = analyze_photo_with_ai(image, user_gps or exif_gps)
    
    # Combine with GPS data
    location_data = {
        "ai_analysis": ai_analysis,
        "gps_sources": {},
        "final_location": None,
        "confidence_score": 0.3
    }
    
    # Prioritize GPS sources
    if user_gps and user_gps.get("accuracy", 1000) < 100:
        location_data["gps_sources"]["user_gps"] = user_gps
        location_data["final_location"] = user_gps
        location_data["confidence_score"] += 0.4
        
    elif exif_gps:
        location_data["gps_sources"]["exif_gps"] = exif_gps  
        location_data["final_location"] = exif_gps
        location_data["confidence_score"] += 0.3
    
    # AI analysis boosts confidence if it suggests Chicago
    if ai_analysis.get("chicago_likelihood", 0) > 0.6:
        location_data["confidence_score"] += 0.2
    
    if ai_analysis.get("landmarks"):
        location_data["confidence_score"] += 0.1
    
    # If no GPS but AI is confident about Chicago, use downtown coordinates
    if not location_data["final_location"] and ai_analysis.get("chicago_likelihood", 0) > 0.7:
        location_data["final_location"] = {
            "latitude": 41.8781,
            "longitude": -87.6278,
            "accuracy": 1000,
            "source": "ai_inference"
        }
        location_data["confidence_score"] += 0.2
    
    location_data["confidence_score"] = min(location_data["confidence_score"], 0.95)
    
    return location_data

def suggest_chicago_coordinates_from_landmarks(landmarks: List[str]) -> Optional[Dict]:
    """
    Map landmark names to specific GPS coordinates
    """
    landmark_coordinates = {
        "Chicago Theater": {"latitude": 41.8781, "longitude": -87.6278},
        "Willis Tower": {"latitude": 41.8789, "longitude": -87.6359},
        "Sears Tower": {"latitude": 41.8789, "longitude": -87.6359},
        "Navy Pier": {"latitude": 41.8917, "longitude": -87.6086},
        "Millennium Park": {"latitude": 41.8826, "longitude": -87.6226},
        "Grant Park": {"latitude": 41.8758, "longitude": -87.6189},
        "Wrigley Field": {"latitude": 41.9484, "longitude": -87.6553},
        "Union Station": {"latitude": 41.8789, "longitude": -87.6406},
        "Art Institute": {"latitude": 41.8796, "longitude": -87.6237},
        "Lincoln Park Zoo": {"latitude": 41.9212, "longitude": -87.6341},
        "Buckingham Fountain": {"latitude": 41.8758, "longitude": -87.6189},
        "State Street": {"latitude": 41.8781, "longitude": -87.6278},
        "Michigan Avenue": {"latitude": 41.8819, "longitude": -87.6278},
        "Lake Michigan": {"latitude": 41.8900, "longitude": -87.6200},
        "Chicago Riverwalk": {"latitude": 41.8885, "longitude": -87.6190}
    }
    
    for landmark in landmarks:
        if landmark in landmark_coordinates:
            coords = landmark_coordinates[landmark].copy()
            coords["source"] = f"landmark_{landmark}"
            coords["accuracy"] = 200  # Landmark-based has moderate accuracy
            return coords
    
    return None
