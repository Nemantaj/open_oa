from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
import os
import traceback
from typing import Optional, List, Dict, Any

from .data import datasets_store
from .jobs import job_store

from examples import project_ENGIE
from openoa.analysis.aep import MonteCarloAEP
from openoa.analysis.electrical_losses import ElectricalLosses
from openoa.analysis.turbine_long_term_gross_energy import TurbineLongTermGrossEnergy
from openoa.analysis.wake_losses import WakeLosses
from openoa.analysis.yaw_misalignment import StaticYawMisalignment

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
)

class AnalysisRequestArgs(BaseModel):
    dataset_id: str = Field(..., description="ID of the dataset uploaded via /api/data/upload")
    num_sim: int = Field(100, description="Number of Monte Carlo simulations to run")

class JobInitiatedResponse(BaseModel):
    job_id: str = Field(..., description="ID to track the analysis progress via /api/jobs/{job_id}")
    status: str
    message: str

def get_plant_from_store(dataset_id: str):
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found. Upload it first via /api/data/upload.")
    return datasets_store[dataset_id]

# ---------------------------------------------------------
# BACKGROUND TASK WORKERS
# ---------------------------------------------------------

def run_aep_background_task(job_id: str, plant, num_sim: int):
    try:
        pa = MonteCarloAEP(plant, reanalysis_products=["era5", "merra2"], time_resolution="ME")
        pa.run(num_sim=num_sim, progress_bar=False)
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = {
            "mean": pa.results.mean().to_dict(),
            "std_dev": pa.results.std().to_dict(),
            "type": "Monte Carlo AEP"
        }
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e) + "\n" + traceback.format_exc()

def run_electrical_losses_background_task(job_id: str, plant, num_sim: int):
    try:
        el = ElectricalLosses(plant=plant, URC_db=False)
        el.run(num_sim=num_sim, progress_bar=False)
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = {
            "mean_electrical_losses": float(el.electrical_losses.mean()),
            "std_electrical_losses": float(el.electrical_losses.std()),
            "type": "Electrical Losses"
        }
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e) + "\n" + traceback.format_exc()

def run_tie_background_task(job_id: str, plant, num_sim: int):
    try:
        tie = TurbineLongTermGrossEnergy(plant, URC_db=False)
        tie.run(num_sim=num_sim, progress_bar=False)
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = {
            "mean_tie": float(tie.plant_gross_energy.mean()),
            "type": "Turbine Ideal Energy"
        }
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e) + "\n" + traceback.format_exc()

def run_wake_losses_background_task(job_id: str, plant):
    try:
        wl = WakeLosses(plant)
        wl.run(progress_bar=False)
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["result"] = {
            "mean_wake_losses": float(wl.plant_wake_losses.mean()),
            "type": "Wake Losses"
        }
    except Exception as e:
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e) + "\n" + traceback.format_exc()

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@router.get("/aep/example")
def run_example_aep():
    """ Runs AEP synchronously on the built-in example dataset. """
    data_path = os.path.join("examples", "data", "la_haute_borne")
    plant = project_ENGIE.prepare(path=data_path, return_value="plantdata")
    
    pa = MonteCarloAEP(
        plant, 
        reanalysis_products=["era5", "merra2"],
        time_resolution="ME",
        reg_model="lin",
        reg_temperature=False,
        reg_wind_direction=False,
    )
    
    pa.run(num_sim=10, progress_bar=False)
    
    return {
        "status": "success",
        "message": "Monte Carlo AEP Analysis completed using La Haute Borne example data.",
        "simulations_run": 10,
        "results_mean": pa.results.mean().to_dict(),
        "results_std": pa.results.std().to_dict()
    }


@router.post("/aep")
def analyze_aep(args: AnalysisRequestArgs, background_tasks: BackgroundTasks):
    plant = get_plant_from_store(args.dataset_id)
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "processing"}
    background_tasks.add_task(run_aep_background_task, job_id, plant, args.num_sim)
    return JobInitiatedResponse(job_id=job_id, status="processing", message="AEP background calculation started.")

@router.post("/electrical-losses")
def analyze_electrical_losses(args: AnalysisRequestArgs, background_tasks: BackgroundTasks):
    plant = get_plant_from_store(args.dataset_id)
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "processing"}
    background_tasks.add_task(run_electrical_losses_background_task, job_id, plant, args.num_sim)
    return JobInitiatedResponse(job_id=job_id, status="processing", message="Electrical Losses background calculation started.")

@router.post("/tie")
def analyze_tie(args: AnalysisRequestArgs, background_tasks: BackgroundTasks):
    plant = get_plant_from_store(args.dataset_id)
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "processing"}
    background_tasks.add_task(run_tie_background_task, job_id, plant, args.num_sim)
    return JobInitiatedResponse(job_id=job_id, status="processing", message="Turbine Ideal Energy (TIE) background calculation started.")

@router.post("/wake-losses")
def analyze_wake_losses(args: AnalysisRequestArgs, background_tasks: BackgroundTasks):
    plant = get_plant_from_store(args.dataset_id)
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "processing"}
    background_tasks.add_task(run_wake_losses_background_task, job_id, plant)
    return JobInitiatedResponse(job_id=job_id, status="processing", message="Wake Losses background calculation started.")

@router.post("/yaw-misalignment")
def analyze_yaw_misalignment(args: AnalysisRequestArgs, background_tasks: BackgroundTasks):
    plant = get_plant_from_store(args.dataset_id)
    job_id = str(uuid.uuid4())
    job_store[job_id] = {"status": "processing"}
    
    # Needs special plotting options in background task 
    def run_yaw_misalignment(job_id, plant):
        try:
            yaw = StaticYawMisalignment(plant)
            yaw.run(progress_bar=False)
            job_store[job_id]["status"] = "completed"
            job_store[job_id]["result"] = {"type": "Static Yaw Misalignment", "status": "completed"}
        except Exception as e:
            job_store[job_id]["status"] = "failed"
            job_store[job_id]["error"] = str(e)
            
    background_tasks.add_task(run_yaw_misalignment, job_id, plant)
    return JobInitiatedResponse(job_id=job_id, status="processing", message="Static Yaw Misalignment background calculation started.")
