from fastapi import APIRouter, HTTPException
from .schema import AirDensityAdjustmentRequest, AirDensityAdjustmentResponse
import openoa.utils.met_data_processing as met
import pandas as pd

router = APIRouter(
    prefix="/api/utils",
    tags=["utils"],
)

@router.post("/air-density-adjusted-wind-speed", response_model=AirDensityAdjustmentResponse)
def adjust_wind_speed(request: AirDensityAdjustmentRequest):
    if len(request.wind_speeds) != len(request.air_densities):
        raise HTTPException(status_code=400, detail="wind_speeds and air_densities must have the same length")
    
    # OpenOA's function expects pandas Series
    ws_series = pd.Series(request.wind_speeds)
    rho_series = pd.Series(request.air_densities)
    
    adjusted = met.air_density_adjusted_wind_speed(wind_speed=ws_series, density=rho_series)
    
    return AirDensityAdjustmentResponse(adjusted_wind_speeds=adjusted.tolist())
