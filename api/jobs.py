from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(
    prefix="/api/jobs",
    tags=["jobs"],
)

# In-memory dictionary to store job statuses and results
# A true production app would use Redis or a Database
job_store: Dict[str, Dict[str, Any]] = {}

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None

@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_data = job_store[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job_data.get("status", "unknown"),
        result=job_data.get("result"),
        error=job_data.get("error")
    )
