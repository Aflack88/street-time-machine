# backend/app/main.py
import os
import io
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import piexif
import uvicorn
from utils import extract_gps_from_exif, find_nearest_historical_image
from stripe_webhook import stripe_webhook_router

app = FastAPI(title="Street Time Machine - Backend")

# CORS - allow your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount or include stripe webhook router
app.include_router(stripe_webhook_router, prefix="/stripe")

@app.post("/process-photo")
async def process_photo(file: UploadFile = File(...)):
    """
    Accepts an image, extracts EXIF GPS (if present), 
    and returns a matched historical image URL + optional alignment metadata.
    """
    contents = await file.read()

    # try to open as PIL image to ensure it's valid
    try:
        image = Image.open(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # extract exif bytes
    exif_bytes = image.info.get("exif", None)
    gps = None
    if exif_bytes:
        try:
            gps = extract_gps_from_exif(exif_bytes)
        except Exception:
            gps = None

    # For MVP, we mock historical lookup with a simple helper that returns a static file path
    # Replace this with your real dataset lookup (spatial DB / S3 + index)
    result = find_nearest_historical_image(gps)

    if not result:
        return JSONResponse(status_code=404, content={"error": "No historical photo found for this location."})

    return {
        "historical_url": result["url"],
        "year": result.get("year"),
        "alignment": result.get("alignment", {}),
    }

@app.get("/historical/{image_name}")
async def historical_image(image_name: str):
    """
    Serves sample historical images from disk. For production, use a CDN or S3.
    """
    static_dir = os.path.join(os.path.dirname(__file__), "static_historical")
    candidate = os.path.join(static_dir, image_name)
    if not os.path.exists(candidate):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(candidate, media_type="image/jpeg")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
