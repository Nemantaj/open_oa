from fastapi import APIRouter
from pydantic import BaseModel, Field

from .data import datasets_store
from openoa.utils import filters

router = APIRouter(
    prefix="/api/qa",
    tags=["qa"],
)

class QAFilterRequest(BaseModel):
    dataset_id: str = Field(..., description="ID of the plant dataset")
    sensor_col: str = Field(..., description="DataFrame column name to check")

@router.post("/flag-unresponsive")
def flag_unresponsive_sensor(request: QAFilterRequest, threshold: int = 3):
    if request.dataset_id not in datasets_store:
        return {"error": "Dataset not found"}
    plant = datasets_store[request.dataset_id]
    
    # We apply this to the SCADA data dataframe for simplicity 
    try:
        flags = filters.unresponsive_flag(plant.scada, threshold, col=[request.sensor_col])
        flag_count = int(flags[request.sensor_col].sum())
        return {"status": "success", "flagged_data_points": flag_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/flag-range")
def flag_range_sensor(request: QAFilterRequest, lower_bound: float, upper_bound: float):
    if request.dataset_id not in datasets_store:
        return {"error": "Dataset not found"}
    plant = datasets_store[request.dataset_id]
    
    try:
        flags = filters.range_flag(plant.scada[request.sensor_col], lower=lower_bound, upper=upper_bound)
        flag_count = int(flags.sum())
        return {"status": "success", "flagged_data_points": flag_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
