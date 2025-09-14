# backend/app/main.py
import os
import io
import json
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import uvicorn
from enhanced_utils import (
    extract_enhanced_metadata, 
    find_best_historical_match, 
    generate_historical_story,
    calculate_confidence_score
)
from stripe_webhook import stripe_webhook_router
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Street Time Machine - Enhanced Backend")

# CORS - allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount stripe webhook router
app.include_router(stripe_webhook_router, prefix="/stripe")

@app.post("/process-photo")
async def process_photo(file: UploadFile = File(...), metadata: str = Form(...)):
    """
    Enhanced photo processing with GPS, heading, visual analysis, and historical matching.
    """
    try:
        # Parse metadata from frontend
        user_metadata = json.loads(metadata)
        gps_data = user_metadata.get("gps")
        heading = user_metadata.get("heading")
        
        if not gps_data:
            raise HTTPException(status_code=400, detail="GPS location required for historical matching")
        
        logger.info(f"Processing photo for location: {gps_data['latitude']}, {gps_data['longitude']}")
        
        # Read and validate image
        contents = await file.read()
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image: {e}")
        
        # Extract enhanced metadata (EXIF + visual features)
        enhanced_metadata = extract_enhanced_metadata(image, contents, gps_data, heading)
        
        # Find best historical match using multiple strategies
        match_result = find_best_historical_match(enhanced_metadata)
        
        if not match_result:
            return JSONResponse(
                status_code=404, 
                content={"error": "No historical photos found for this location. Try a different street or check back as we add more data!"}
            )
        
        # Calculate confidence score
        confidence = calculate_confidence_score(enhanced_metadata, match_result)
        
        # Generate contextual story and facts
        story = generate_historical_story(match_result, enhanced_metadata)
        
        # Prepare response
        response_data = {
            "historical_url": match_result["url"],
            "year": match_result.get("year"),
            "confidence": confidence,
            "distance_meters": match_result.get("distance_meters", 0),
            "story": story,
            "match_details": {
                "method": match_result.get("match_method", "gps_proximity"),
                "landmarks_matched": match_result.get("landmarks_matched", []),
                "viewing_angle_match": match_result.get("angle_similarity", 0)
            }
        }
        
        logger.info(f"Successful match: {match_result['url']} with {confidence}% confidence")
        return response_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata format")
    except Exception as e:
        logger.error(f"Error processing photo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.get("/historical/{image_name}")
async def historical_image(image_name: str):
    """
    Serves historical images. In production, use CDN/S3.
    """
    static_dir = os.path.join(os.path.dirname(__file__), "static_historical")
    candidate = os.path.join(static_dir, image_name)
    
    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail="Historical image not found")
    
    return FileResponse(candidate, media_type="image/jpeg")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0"}

@app.get("/api/locations/{lat}/{lon}")
async def get_location_info(lat: float, lon: float):
    """
    Get available historical data for a specific location
    """
    try:
        # This would query your historical database
        # For now, return mock data
        return {
            "available_years": [1890, 1920, 1950, 1980],
            "photo_count": 12,
            "landmarks": ["Chicago Theater", "State Street", "Loop District"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
