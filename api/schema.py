from pydantic import BaseModel, Field
from typing import List

class AirDensityAdjustmentRequest(BaseModel):
    wind_speeds: List[float] = Field(..., description="List of wind speeds (m/s)")
    air_densities: List[float] = Field(..., description="List of air densities (kg/m^3)")

class AirDensityAdjustmentResponse(BaseModel):
    adjusted_wind_speeds: List[float] = Field(..., description="List of density-adjusted wind speeds (m/s)")
