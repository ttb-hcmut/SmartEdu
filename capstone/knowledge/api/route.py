from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import os
from core.dependencies import (
    get_ingestion_service
)
router = APIRouter(tags=["Knowledge"])

class CourseIngestionRequest(BaseModel):
    course_name :str= "Machine Learning"
    slide_files: List[str]
    textbook_files: List[str]
    reset: bool = True

@router.post("/ingest-course")
async def ingest_course(
    req: CourseIngestionRequest,
    background_tasks: BackgroundTasks,
    service = Depends(get_ingestion_service)
):
    service.validate_files(req.slide_files + req.textbook_files)

    
    background_tasks.add_task(service.run, req)
    
    return {
        "status": "accepted",
        "message": f"Course {req.course_name} ingestion started in background",
        "details": {
            "slides_count": len(req.slide_files),
            "textbooks_count": len(req.textbook_files)
        }
    }


