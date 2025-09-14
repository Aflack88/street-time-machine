# backend/app/curation_api.py
"""
API endpoints for managing auto-curation system
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, timedelta
import logging

from database import get_db, HistoricalPhoto, CurationLog, PhotoQualityFeedback
from photo_curator import AIPhotoCurator, schedule_curation_cycles
import json

logger = logging.getLogger(__name__)

curation_router = APIRouter(prefix="/curation", tags=["Auto-Curation"])

@curation_router.post("/run-cycle")
async def run_curation_cycle(
    max_photos: int = 25,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Manually trigger a curation cycle
    """
    try:
        # Run curation in background
        background_tasks.add_task(execute_curation_cycle, max_photos, db)
        
        return {
            "message": f"Curation cycle started for {max_photos} photos",
            "status": "running",
            "estimated_duration_minutes": max_photos * 0.5  # Rough estimate
        }
        
    except Exception as e:
        logger.error(f"Failed to start curation cycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@curation_router.get("/status")
async def get_curation_status(db: Session = Depends(get_db)):
    """
    Get the status of the auto-curation system
    """
    try:
        # Get recent curation logs
        recent_logs = db.query(CurationLog).order_by(
            CurationLog.cycle_date.desc()
        ).limit(5).all()
        
        # Get database statistics
        total_photos = db.query(HistoricalPhoto).count()
        auto_curated = db.query(HistoricalPhoto).filter(
            HistoricalPhoto.auto_curated == True
        ).count()
        
        # Calculate recent performance
        if recent_logs:
            latest_log = recent_logs[0]
            avg_success_rate = sum(log.success_rate or 0 for log in recent_logs) / len(recent_logs)
            total_discovered_recently = sum(log.photos_discovered or 0 for log in recent_logs)
            total_stored_recently = sum(log.photos_stored or 0 for log in recent_logs)
        else:
            latest_log = None
            avg_success_rate = 0
            total_discovered_recently = 0
            total_stored_recently = 0
        
        return {
            "database_stats": {
                "total_photos": total_photos,
                "auto_curated_photos": auto_curated,
                "manual_photos": total_photos - auto_curated,
                "auto_curation_percentage": (auto_curated / max(total_photos, 1)) * 100
            },
            "recent_performance": {
                "last_cycle": latest_log.cycle_date if latest_log else None,
                "avg_success_rate": round(avg_success_rate, 2),
                "photos_discovered_recently": total_discovered_recently,
                "photos_stored_recently": total_stored_recently
            },
            "system_health": {
                "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "flickr_configured": bool(os.getenv("FLICKR_API_KEY")),
                "last_successful_cycle": latest_log.cycle_date if latest_log and latest_log.photos_stored > 0 else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting curation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@curation_router.get("/logs")
async def get_curation_logs(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recent curation cycle logs
    """
    try:
        logs = db.query(CurationLog).order_by(
            CurationLog.cycle_date.desc()
        ).limit(limit).all()
        
        log_data = []
        for log in logs:
            log_data.append({
                "id": str(log.id),
                "cycle_date": log.cycle_date.isoformat(),
                "photos_discovered": log.photos_discovered,
                "photos_processed": log.photos_processed,
                "photos_approved": log.photos_approved,
                "photos_stored": log.photos_stored,
                "duration_seconds": log.duration_seconds,
                "success_rate": round(log.success_rate or 0, 2),
                "sources": {
                    "library_of_congress": log.library_of_congress_count,
                    "flickr": log.flickr_count,
                    "wikimedia": log.wikimedia_count,
                    "unsplash": log.unsplash_count
                },
                "quality_metrics": {
                    "avg_chicago_relevance": round(log.avg_chicago_relevance or 0, 1),
                    "avg_image_quality": round(log.avg_image_quality or 0, 1),
                    "avg_historical_value": round(log.avg_historical_value or 0, 1)
                },
                "error_count": log.error_count
            })
        
        return {"logs": log_data}
        
    except Exception as e:
        logger.error(f"Error getting curation logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@curation_router.get("/photos/recent")
async def get_recently_curated_photos(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recently auto-curated photos
    """
    try:
        photos = db.query(HistoricalPhoto).filter(
            HistoricalPhoto.auto_curated == True
        ).order_by(
            HistoricalPhoto.curation_date.desc()
        ).limit(limit).all()
        
        photo_data = []
        for photo in photos:
            ai_analysis = {}
            if photo.ai_analysis_data:
                try:
                    ai_analysis = json.loads(photo.ai_analysis_data)
                except:
                    pass
            
            photo_data.append({
                "id": str(photo.id),
                "filename": photo.filename,
                "title": photo.title,
                "year": photo.year,
                "source": photo.source,
                "source_url": photo.source_url,
                "curation_date": photo.curation_date.isoformat() if photo.curation_date else None,
                "location": {
                    "latitude": photo.latitude,
                    "longitude": photo.longitude,
                    "accuracy": photo.location_accuracy
                },
                "landmarks": json.loads(photo.landmarks) if photo.landmarks else [],
                "quality_scores": {
                    "image_quality": photo.image_quality_score,
                    "historical_interest": photo.historical_interest_score,
                    "chicago_relevance": ai_analysis.get("chicago_relevance", 0),
                },
                "ai_approved": photo.approved_by_ai,
                "needs_review": photo.manual_review_needed
            })
        
        return {"photos": photo_data}
        
    except Exception as e:
        logger.error(f"Error getting recent photos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@curation_router.post("/photos/{photo_id}/feedback")
async def submit_photo_feedback(
    photo_id: str,
    feedback_type: str,
    rating: int,
    comments: str = "",
    db: Session = Depends(get_db)
):
    """
    Submit feedback on auto-curated photos to improve AI
    """
    try:
        # Validate inputs
        if feedback_type not in ["quality", "relevance", "accuracy"]:
            raise HTTPException(status_code=400, detail="Invalid feedback type")
        
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Check if photo exists
        photo = db.query(HistoricalPhoto).filter(HistoricalPhoto.id == photo_id).first()
        if not photo:
            raise HTTPException(status_code=404, detail="Photo not found")
        
        # Create feedback record
        feedback = PhotoQualityFeedback(
            photo_id=photo_id,
            feedback_type=feedback_type,
            rating=rating,
            comments=comments,
            reporter_type="user"
        )
        
        db.add(feedback)
        db.commit()
        
        # Update photo's user rating
        update_photo_ratings(db, photo_id)
        
        return {
            "message": "Feedback submitted successfully",
            "feedback_id": str(feedback.id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@curation_router.post("/schedule/daily")
async def schedule_daily_curation(
    enabled: bool = True,
    max_photos_per_day: int = 50,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Enable/disable daily automatic curation
    """
    try:
        if enabled:
            # In production, you'd use a proper task scheduler like Celery
            # For now, we'll simulate with background tasks
            background_tasks.add_task(schedule_daily_curation_task, max_photos_per_day)
            
            return {
                "message": "Daily curation scheduled",
                "max_photos_per_day": max_photos_per_day,
                "status": "enabled"
            }
        else:
            return {
                "message": "Daily curation disabled",
                "status": "disabled"
            }
            
    except Exception as e:
        logger.error(f"Error scheduling daily curation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@curation_router.get("/analytics")
async def get_curation_analytics(
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get analytics on curation performance
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get logs from the specified period
        logs = db.query(CurationLog).filter(
            CurationLog.cycle_date >= cutoff_date
        ).all()
        
        if not logs:
            return {"message": "No curation data available for the specified period"}
        
        # Calculate analytics
        total_cycles = len(logs)
        total_discovered = sum(log.photos_discovered or 0 for log in logs)
        total_processed = sum(log.photos_processed or 0 for log in logs)
        total_stored = sum(log.photos_stored or 0 for log in logs)
        
        avg_success_rate = sum(log.success_rate or 0 for log in logs) / total_cycles
        avg_cycle_duration = sum(log.duration_seconds or 0 for log in logs) / total_cycles
        
        # Source breakdown
        source_stats = {
            "library_of_congress": sum(log.library_of_congress_count or 0 for log in logs),
            "flickr": sum(log.flickr_count or 0 for log in logs),
            "wikimedia": sum(log.wikimedia_count or 0 for log in logs),
            "unsplash": sum(log.unsplash_count or 0 for log in logs)
        }
        
        # Quality metrics
        quality_logs = [log for log in logs if log.avg_chicago_relevance]
        if quality_logs:
            avg_chicago_relevance = sum(log.avg_chicago_relevance for log in quality_logs) / len(quality_logs)
            avg_image_quality = sum(log.avg_image_quality for log in quality_logs) / len(quality_logs)
            avg_historical_value = sum(log.avg_historical_value for log in quality_logs) / len(quality_logs)
        else:
            avg_chicago_relevance = avg_image_quality = avg_historical_value = 0
        
        return {
            "period_summary": {
                "days_analyzed": days_back,
                "total_cycles": total_cycles,
                "total_photos_discovered": total_discovered,
                "total_photos_processed": total_processed,
                "total_photos_stored": total_stored,
                "overall_success_rate": round(avg_success_rate, 2)
            },
            "performance_metrics": {
                "avg_cycle_duration_minutes": round(avg_cycle_duration / 60, 2),
                "photos_per_cycle": round(total_stored / max(total_cycles, 1), 1),
                "discovery_to_storage_ratio": round((total_stored / max(total_discovered, 1)) * 100, 1)
            },
            "source_breakdown": source_stats,
            "quality_metrics": {
                "avg_chicago_relevance": round(avg_chicago_relevance, 1),
                "avg_image_quality": round(avg_image_quality, 1),
                "avg_historical_value": round(avg_historical_value, 1)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting curation analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def execute_curation_cycle(max_photos: int, db: Session):
    """
    Execute a curation cycle and log results
    """
    try:
        curator = AIPhotoCurator()
        results = curator.run_curation_cycle(max_photos)
        
        # Log results to database
        log_entry = CurationLog(
            photos_discovered=results.get("discovered", 0),
            photos_processed=results.get("processed", 0),
            photos_stored=results.get("stored", 0),
            duration_seconds=results.get("duration_minutes", 0) * 60,
            success_rate=(results.get("stored", 0) / max(results.get("processed", 1), 1)) * 100
        )
        
        db.add(log_entry)
        db.commit()
        
        logger.info(f"Curation cycle completed: {results}")
        
    except Exception as e:
        logger.error(f"Curation cycle execution failed: {e}")

def update_photo_ratings(db: Session, photo_id: str):
    """
    Update photo's average user rating based on feedback
    """
    try:
        feedbacks = db.query(PhotoQualityFeedback).filter(
            PhotoQualityFeedback.photo_id == photo_id
        ).all()
        
        if feedbacks:
            avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
            
            photo = db.query(HistoricalPhoto).filter(HistoricalPhoto.id == photo_id).first()
            if photo:
                photo.user_rating_avg = avg_rating
                photo.user_rating_count = len(feedbacks)
                db.commit()
                
    except Exception as e:
        logger.error(f"Error updating photo ratings: {e}")

async def schedule_daily_curation_task(max_photos: int):
    """
    Background task for daily curation (simplified version)
    In production, use proper task scheduler like Celery
    """
    try:
        import asyncio
        await asyncio.sleep(24 * 60 * 60)  # Wait 24 hours
        
        # Run curation
        results = schedule_curation_cycles()
        logger.info(f"Scheduled daily curation completed: {results}")
        
    except Exception as e:
        logger.error(f"Daily curation task failed: {e}")
