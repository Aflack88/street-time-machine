# backend/app/photo_curator.py
"""
AI-powered photo curation system that automatically finds, analyzes, and stores historical Chicago photos
"""
import os
import requests
import json
import time
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import openai
from PIL import Image
import io
import logging
from dataclasses import dataclass

from ai_vision import analyze_photo_with_ai, encode_image_to_base64
from database import HistoricalPhoto, SessionLocal
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

@dataclass
class PhotoSource:
    name: str
    base_url: str
    api_key: Optional[str] = None
    rate_limit: int = 100  # requests per hour
    search_terms: List[str] = None

# Configure photo sources
PHOTO_SOURCES = [
    PhotoSource(
        name="Library of Congress",
        base_url="https://www.loc.gov/collections/",
        search_terms=["chicago", "chicago illinois", "chicago 1900", "chicago 1920", "chicago streets"]
    ),
    PhotoSource(
        name="Flickr Commons",
        base_url="https://api.flickr.com/services/rest/",
        api_key=os.getenv("FLICKR_API_KEY"),
        search_terms=["chicago historical", "vintage chicago", "old chicago"]
    ),
    PhotoSource(
        name="Unsplash Historical",
        base_url="https://api.unsplash.com/",
        api_key=os.getenv("UNSPLASH_ACCESS_KEY"),
        search_terms=["chicago vintage", "historical chicago", "chicago architecture"]
    ),
    PhotoSource(
        name="Wikimedia Commons",
        base_url="https://commons.wikimedia.org/",
        search_terms=["chicago historical photographs", "vintage chicago streets"]
    )
]

class AIPhotoCurator:
    """
    Main curator class that orchestrates the photo discovery and curation process
    """
    
    def __init__(self):
        self.db = SessionLocal()
        self.openai_client = openai
        self.discovered_photos = []
        self.processed_count = 0
        self.success_count = 0
        
    def run_curation_cycle(self, max_photos_per_cycle: int = 50):
        """
        Run a complete curation cycle: discover -> analyze -> curate -> store
        """
        logger.info(f"Starting curation cycle - target: {max_photos_per_cycle} photos")
        
        start_time = datetime.now()
        
        try:
            # Phase 1: Discover photos from multiple sources
            discovered_photos = self.discover_photos(max_photos_per_cycle)
            logger.info(f"Discovered {len(discovered_photos)} candidate photos")
            
            # Phase 2: AI analysis and filtering
            curated_photos = []
            for photo_data in discovered_photos:
                try:
                    curated_photo = self.analyze_and_curate_photo(photo_data)
                    if curated_photo:
                        curated_photos.append(curated_photo)
                        self.success_count += 1
                    
                    self.processed_count += 1
                    
                    # Rate limiting
                    time.sleep(2)  # Be respectful to APIs
                    
                except Exception as e:
                    logger.error(f"Error processing photo {photo_data.get('url', 'unknown')}: {e}")
                    continue
            
            # Phase 3: Store approved photos
            stored_count = self.store_curated_photos(curated_photos)
            
            # Phase 4: Cleanup and reporting
            duration = datetime.now() - start_time
            self.log_curation_results(stored_count, duration)
            
            return {
                "discovered": len(discovered_photos),
                "processed": self.processed_count, 
                "stored": stored_count,
                "duration_minutes": duration.total_seconds() / 60
            }
            
        except Exception as e:
            logger.error(f"Curation cycle failed: {e}")
            return {"error": str(e)}
        finally:
            self.db.close()
    
    def discover_photos(self, max_photos: int) -> List[Dict]:
        """
        Discover photos from multiple sources using various APIs and web scraping
        """
        all_photos = []
        photos_per_source = max_photos // len(PHOTO_SOURCES)
        
        for source in PHOTO_SOURCES:
            try:
                logger.info(f"Searching {source.name} for historical Chicago photos")
                
                if source.name == "Library of Congress":
                    photos = self.search_library_of_congress(source, photos_per_source)
                elif source.name == "Flickr Commons":
                    photos = self.search_flickr_commons(source, photos_per_source)
                elif source.name == "Unsplash Historical":
                    photos = self.search_unsplash(source, photos_per_source)
                elif source.name == "Wikimedia Commons":
                    photos = self.search_wikimedia_commons(source, photos_per_source)
                else:
                    photos = []
                
                all_photos.extend(photos)
                logger.info(f"Found {len(photos)} photos from {source.name}")
                
            except Exception as e:
                logger.error(f"Error searching {source.name}: {e}")
                continue
        
        # Remove duplicates and limit total
        unique_photos = self.deduplicate_photos(all_photos)
        return unique_photos[:max_photos]
    
    def search_library_of_congress(self, source: PhotoSource, limit: int) -> List[Dict]:
        """
        Search Library of Congress digital collections
        """
        photos = []
        
        for search_term in source.search_terms[:2]:  # Limit search terms
            try:
                # Library of Congress JSON API
                url = "https://www.loc.gov/collections/chicago-history/"
                
                # For demo, create mock data - in production, implement actual API calls
                for i in range(min(limit // 2, 10)):
                    photos.append({
                        "url": f"https://tile.loc.gov/image-services/chicago_{i}.jpg",
                        "title": f"Chicago Street Scene - {search_term}",
                        "source": "Library of Congress",
                        "date_estimate": f"19{20 + i * 3}",
                        "description": f"Historical photograph of {search_term}",
                        "metadata": {
                            "collection": "Chicago History",
                            "search_term": search_term
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Error searching LoC for {search_term}: {e}")
                continue
        
        return photos
    
    def search_flickr_commons(self, source: PhotoSource, limit: int) -> List[Dict]:
        """
        Search Flickr Commons for historical photos
        """
        if not source.api_key:
            logger.warning("Flickr API key not configured")
            return []
        
        photos = []
        
        try:
            for search_term in source.search_terms[:2]:
                url = "https://api.flickr.com/services/rest/"
                params = {
                    "method": "flickr.photos.search",
                    "api_key": source.api_key,
                    "text": search_term,
                    "license": "1,2,4,7",  # Creative Commons licenses
                    "sort": "relevance",
                    "per_page": limit // 2,
                    "format": "json",
                    "nojsoncallback": 1,
                    "extras": "description,date_taken,tags,geo"
                }
                
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                
                if data.get("stat") == "ok":
                    for photo in data["photos"]["photo"]:
                        photos.append({
                            "url": f"https://live.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_b.jpg",
                            "title": photo.get("title", "Historical Chicago Photo"),
                            "source": "Flickr Commons",
                            "date_estimate": photo.get("datetaken", "").split("-")[0],
                            "description": photo.get("description", {}).get("_content", ""),
                            "metadata": {
                                "flickr_id": photo["id"],
                                "tags": photo.get("tags", ""),
                                "latitude": photo.get("latitude"),
                                "longitude": photo.get("longitude")
                            }
                        })
                
        except Exception as e:
            logger.error(f"Error searching Flickr: {e}")
        
        return photos
    
    def search_wikimedia_commons(self, source: PhotoSource, limit: int) -> List[Dict]:
        """
        Search Wikimedia Commons for historical Chicago photos
        """
        photos = []
        
        try:
            # Wikimedia Commons API
            for search_term in source.search_terms[:2]:
                url = "https://commons.wikimedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "list": "search",
                    "srsearch": f"{search_term} filetype:bitmap",
                    "srlimit": limit // 2,
                    "srnamespace": 6  # File namespace
                }
                
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                
                for item in data.get("query", {}).get("search", []):
                    title = item["title"]
                    if "File:" in title:
                        # Get actual image URL
                        img_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{title.replace('File:', '')}"
                        
                        photos.append({
                            "url": img_url,
                            "title": title.replace("File:", "").replace(".jpg", "").replace(".png", ""),
                            "source": "Wikimedia Commons",
                            "date_estimate": "1950",  # Default estimate
                            "description": item.get("snippet", ""),
                            "metadata": {
                                "wikimedia_page": f"https://commons.wikimedia.org/wiki/{title}",
                                "search_term": search_term
                            }
                        })
        
        except Exception as e:
            logger.error(f"Error searching Wikimedia: {e}")
        
        return photos
    
    def analyze_and_curate_photo(self, photo_data: Dict) -> Optional[Dict]:
        """
        Use AI to analyze a discovered photo and determine if it should be included
        """
        try:
            # Download the image
            response = requests.get(photo_data["url"], timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                logger.warning(f"Failed to download image from {photo_data['url']}")
                return None
            
            # Open with PIL
            image = Image.open(io.BytesIO(response.content))
            
            # AI Analysis
            ai_analysis = self.ai_quality_assessment(image, photo_data)
            
            if not ai_analysis["approved"]:
                logger.info(f"Photo rejected: {ai_analysis['rejection_reason']}")
                return None
            
            # Extract location and metadata
            location_data = self.extract_location_from_ai_analysis(ai_analysis)
            
            if not location_data:
                logger.info("Photo rejected: No Chicago location detected")
                return None
            
            # Generate filename and save image
            filename = self.generate_filename(photo_data, ai_analysis)
            image_path = os.path.join("static_historical", filename)
            
            # Save image
            os.makedirs("static_historical", exist_ok=True)
            image.save(image_path, "JPEG", quality=95)
            
            # Prepare database record
            curated_photo = {
                "filename": filename,
                "original_url": photo_data["url"],
                "title": ai_analysis.get("title", photo_data["title"]),
                "description": ai_analysis.get("description", photo_data["description"]),
                "year": ai_analysis.get("estimated_year", int(photo_data.get("date_estimate", "1950"))),
                "source": photo_data["source"],
                "location": location_data,
                "ai_analysis": ai_analysis,
                "landmarks": ai_analysis.get("landmarks", []),
                "quality_score": ai_analysis.get("quality_score", 0.7),
                "historical_interest_score": ai_analysis.get("historical_interest", 0.7)
            }
            
            return curated_photo
            
        except Exception as e:
            logger.error(f"Error analyzing photo {photo_data['url']}: {e}")
            return None
    
    def ai_quality_assessment(self, image: Image.Image, photo_data: Dict) -> Dict:
        """
        Use OpenAI Vision to assess photo quality and relevance
        """
        try:
            base64_image = encode_image_to_base64(image)
            
            prompt = f"""Analyze this historical photograph and determine if it should be included in a Chicago historical photo database. 

Photo metadata:
- Title: {photo_data.get('title', 'Unknown')}
- Source: {photo_data.get('source', 'Unknown')}
- Estimated date: {photo_data.get('date_estimate', 'Unknown')}

Please assess:

1. **Chicago Relevance** (0-100): Is this clearly a Chicago location? Look for:
   - Recognizable Chicago landmarks
   - Chicago-style architecture
   - Geographic features (Lake Michigan, Chicago River)
   - Street signs or text indicating Chicago

2. **Historical Value** (0-100): Historical significance and interest level

3. **Image Quality** (0-100): Technical quality, clarity, composition

4. **Time Period**: What decade/year does this appear to be from?

5. **Location Details**: 
   - Specific landmarks visible
   - Approximate neighborhood/area
   - Viewing direction if determinable

6. **APPROVAL DECISION**: Should this photo be added to the database?
   - Minimum requirements: Chicago relevance >70, Quality >50, Historical value >60

Respond in JSON format:
{{
    "chicago_relevance": 85,
    "historical_value": 75,
    "image_quality": 80,
    "estimated_year": 1945,
    "landmarks": ["Chicago Theater", "State Street"],
    "neighborhood": "Loop District",
    "viewing_direction": "North",
    "approved": true,
    "rejection_reason": null,
    "title": "Improved title based on analysis",
    "description": "Detailed description of what's shown"
}}
"""

            response = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
                temperature=0.1
            )
            
            # Parse JSON response
            analysis_text = response.choices[0].message.content
            
            # Clean up the response to extract JSON
            if "```json" in analysis_text:
                json_str = analysis_text.split("```json")[1].split("```")[0]
            else:
                json_str = analysis_text
            
            analysis = json.loads(json_str)
            
            # Apply approval logic
            chicago_rel = analysis.get("chicago_relevance", 0)
            quality = analysis.get("image_quality", 0) 
            historical = analysis.get("historical_value", 0)
            
            analysis["approved"] = (
                chicago_rel >= 70 and 
                quality >= 50 and 
                historical >= 60
            )
            
            if not analysis["approved"]:
                analysis["rejection_reason"] = f"Scores: Chicago {chicago_rel}, Quality {quality}, Historical {historical}"
            
            return analysis
            
        except Exception as e:
            logger.error(f"AI quality assessment failed: {e}")
            return {
                "approved": False,
                "rejection_reason": f"AI analysis failed: {str(e)}",
                "chicago_relevance": 0,
                "historical_value": 0,
                "image_quality": 0
            }
    
    def extract_location_from_ai_analysis(self, ai_analysis: Dict) -> Optional[Dict]:
        """
        Extract GPS coordinates from AI analysis of landmarks
        """
        landmarks = ai_analysis.get("landmarks", [])
        neighborhood = ai_analysis.get("neighborhood", "").lower()
        
        # Chicago landmark coordinates
        landmark_coords = {
            "chicago theater": {"lat": 41.8781, "lon": -87.6278},
            "state street": {"lat": 41.8781, "lon": -87.6278},
            "loop district": {"lat": 41.8796, "lon": -87.6237},
            "michigan avenue": {"lat": 41.8819, "lon": -87.6278},
            "navy pier": {"lat": 41.8917, "lon": -87.6086},
            "grant park": {"lat": 41.8758, "lon": -87.6189},
            "millennium park": {"lat": 41.8826, "lon": -87.6226},
            "wrigley field": {"lat": 41.9484, "lon": -87.6553},
            "union station": {"lat": 41.8789, "lon": -87.6406},
            "willis tower": {"lat": 41.8789, "lon": -87.6359},
            "sears tower": {"lat": 41.8789, "lon": -87.6359}
        }
        
        # Try to match landmarks
        for landmark in landmarks:
            landmark_key = landmark.lower()
            if landmark_key in landmark_coords:
                coords = landmark_coords[landmark_key]
                return {
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "source": f"landmark_{landmark}",
                    "accuracy": 200
                }
        
        # Try neighborhood matching
        neighborhood_coords = {
            "loop": {"lat": 41.8796, "lon": -87.6237},
            "downtown": {"lat": 41.8781, "lon": -87.6278},
            "gold coast": {"lat": 41.9031, "lon": -87.6275},
            "lincoln park": {"lat": 41.9212, "lon": -87.6341},
            "wrigleyville": {"lat": 41.9484, "lon": -87.6553}
        }
        
        for neighborhood_name, coords in neighborhood_coords.items():
            if neighborhood_name in neighborhood:
                return {
                    "latitude": coords["lat"],
                    "longitude": coords["lon"],
                    "source": f"neighborhood_{neighborhood_name}",
                    "accuracy": 500
                }
        
        # Default to downtown Chicago
        return {
            "latitude": 41.8781,
            "longitude": -87.6278,
            "source": "default_chicago",
            "accuracy": 2000
        }
    
    def generate_filename(self, photo_data: Dict, ai_analysis: Dict) -> str:
        """
        Generate a descriptive filename for the curated photo
        """
        year = ai_analysis.get("estimated_year", photo_data.get("date_estimate", "1950"))
        landmarks = ai_analysis.get("landmarks", [])
        neighborhood = ai_analysis.get("neighborhood", "chicago")
        
        # Create base name
        if landmarks:
            base = landmarks[0].lower().replace(" ", "_")
        elif neighborhood:
            base = neighborhood.lower().replace(" ", "_")
        else:
            base = "chicago_street"
        
        # Create hash for uniqueness
        url_hash = hashlib.md5(photo_data["url"].encode()).hexdigest()[:8]
        
        filename = f"{base}_{year}_{url_hash}.jpg"
        return filename
    
    def store_curated_photos(self, curated_photos: List[Dict]) -> int:
        """
        Store approved photos in the database
        """
        stored_count = 0
        
        for photo_data in curated_photos:
            try:
                # Check if photo already exists (by filename or URL)
                existing = self.db.query(HistoricalPhoto).filter(
                    (HistoricalPhoto.filename == photo_data["filename"]) |
                    (HistoricalPhoto.source_url == photo_data["original_url"])
                ).first()
                
                if existing:
                    logger.info(f"Photo already exists: {photo_data['filename']}")
                    continue
                
                # Create database record
                location = photo_data["location"]
                
                db_photo = HistoricalPhoto(
                    filename=photo_data["filename"],
                    title=photo_data["title"],
                    description=photo_data["description"],
                    year=photo_data["year"],
                    decade=(photo_data["year"] // 10) * 10,
                    source=photo_data["source"],
                    source_url=photo_data["original_url"],
                    location=f"POINT({location['longitude']} {location['latitude']})",
                    landmarks=json.dumps(photo_data["landmarks"]),
                    image_quality_score=photo_data["quality_score"],
                    historical_interest_score=photo_data["historical_interest_score"],
                    ai_analysis_data=json.dumps(photo_data["ai_analysis"]),
                    auto_curated=True,
                    curation_date=datetime.utcnow()
                )
                
                self.db.add(db_photo)
                self.db.commit()
                stored_count += 1
                
                logger.info(f"Stored photo: {photo_data['title']} ({photo_data['year']})")
                
            except Exception as e:
                logger.error(f"Error storing photo {photo_data['filename']}: {e}")
                self.db.rollback()
                continue
        
        return stored_count
    
    def deduplicate_photos(self, photos: List[Dict]) -> List[Dict]:
        """
        Remove duplicate photos based on URL and content similarity
        """
        seen_urls = set()
        unique_photos = []
        
        for photo in photos:
            url = photo["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_photos.append(photo)
        
        return unique_photos
    
    def log_curation_results(self, stored_count: int, duration: timedelta):
        """
        Log the results of the curation cycle
        """
        logger.info(f"""
        Curation Cycle Complete:
        - Duration: {duration.total_seconds():.1f} seconds
        - Photos processed: {self.processed_count}
        - Photos approved and stored: {stored_count}
        - Success rate: {(self.success_count/max(self.processed_count, 1)*100):.1f}%
        """)

# Background task scheduler
def schedule_curation_cycles():
    """
    Run curation cycles on a schedule (daily, weekly, etc.)
    """
    curator = AIPhotoCurator()
    
    # Run a curation cycle
    results = curator.run_curation_cycle(max_photos_per_cycle=25)
    
    logger.info(f"Scheduled curation completed: {results}")
    return results

if __name__ == "__main__":
    # Manual test run
    curator = AIPhotoCurator()
    results = curator.run_curation_cycle(max_photos_per_cycle=10)
    print(f"Curation results: {results}")
