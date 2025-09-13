# backend/app/utils.py
import piexif
from typing import Optional, Dict
import os

def dms_to_dd(dms, ref):
    # Convert (deg, min, sec) to decimal degrees
    deg, minute, sec = dms
    dd = deg + minute / 60.0 + sec / 3600.0
    if ref in ['S', 'W']:
        dd = -dd
    return dd

def extract_gps_from_exif(exif_bytes) -> Optional[Dict[str, float]]:
    """
    Parse EXIF bytes and extract GPS coordinates if available.
    Returns dict: {"lat": float, "lon": float}
    """
    exif_dict = piexif.load(exif_bytes)
    gps_ifd = exif_dict.get("GPS", {})
    if not gps_ifd:
        return None

    # GPSLatitude, GPSLatitudeRef, GPSLongitude, GPSLongitudeRef
    lat = gps_ifd.get(piexif.GPSIFD.GPSLatitude)
    lat_ref = gps_ifd.get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode()
    lon = gps_ifd.get(piexif.GPSIFD.GPSLongitude)
    lon_ref = gps_ifd.get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode()

    if not lat or not lon:
        return None

    # convert rationals to floats
    def rational_to_float(tup):
        return float(tup[0]) / float(tup[1])

    lat_vals = [rational_to_float(x) for x in lat]
    lon_vals = [rational_to_float(x) for x in lon]

    lat_dd = dms_to_dd(lat_vals, lat_ref)
    lon_dd = dms_to_dd(lon_vals, lon_ref)

    return {"lat": lat_dd, "lon": lon_dd}

def find_nearest_historical_image(gps):
    """
    Mocked: returns a static image from static_historical based on input GPS.
    Replace with a real spatial lookup (PostGIS, HNSW index, S3 lookup).
    """
    static_dir = os.path.join(os.path.dirname(__file__), "static_historical")
    # naive behavior: always return a fixed sample image for demo
    sample = "chicago_1950_sample.jpg"  # put this file in static_historical
    url = f"/historical/{sample}"
    # mock year and alignment
    return {"url": url, "year": 1950, "alignment": {"transform": "none"}}
