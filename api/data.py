from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import ValidationError
import pandas as pd
import uuid
import json
import io
from .schema import DatasetResponse
from openoa.plant import PlantData

router = APIRouter(
    prefix="/api/data",
    tags=["data"],
)

# In-memory dictionary to store PlantData objects
# Note: For production, consider serializing and storing securely 
datasets_store = {}

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    metadata: str = Form(..., description="JSON string containing PlantData metadata map"),
    scada: UploadFile = File(..., description="CSV file with SCADA data"),
    meter: UploadFile = File(..., description="CSV file with Meter data"),
    curtail: UploadFile = File(..., description="CSV file with Curtailment data"),
    asset: UploadFile = File(..., description="CSV file with Asset data"),
    reanalysis_era5: UploadFile = None,
    reanalysis_merra2: UploadFile = None
):
    try:
        # 1. Parse Metadata
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format for metadata")

        # 2. Read CSVs into Pandas DataFrames
        scada_df = pd.read_csv(io.StringIO((await scada.read()).decode('utf-8')))
        meter_df = pd.read_csv(io.StringIO((await meter.read()).decode('utf-8')))
        curtail_df = pd.read_csv(io.StringIO((await curtail.read()).decode('utf-8')))
        asset_df = pd.read_csv(io.StringIO((await asset.read()).decode('utf-8')))
        
        reanalysis_dict = {}
        if reanalysis_era5:
            reanalysis_dict['era5'] = pd.read_csv(io.StringIO((await reanalysis_era5.read()).decode('utf-8')))
        if reanalysis_merra2:
            reanalysis_dict['merra2'] = pd.read_csv(io.StringIO((await reanalysis_merra2.read()).decode('utf-8')))
            
        # 3. Initialize PlantData
        # (Assuming the files are pre-formatted correctly as required by OpenOA core libraries)
        plant_data = PlantData(
            analysis_type="MonteCarloAEP", 
            metadata=meta_dict,
            scada=scada_df,
            meter=meter_df,
            curtail=curtail_df,
            asset=asset_df,
            reanalysis=reanalysis_dict
        )
        
        # 4. Store in memory
        dataset_id = str(uuid.uuid4())
        datasets_store[dataset_id] = plant_data
        
        return DatasetResponse(
            dataset_id=dataset_id,
            status="success",
            message=f"Dataset successfully created with {len(scada_df)} SCADA rows."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing dataset: {str(e)}")
