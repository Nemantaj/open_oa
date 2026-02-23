from fastapi import APIRouter
from openoa.examples import project_ENGIE
from openoa.analysis.aep import MonteCarloAEP
import os

router = APIRouter(
    prefix="/api/analysis",
    tags=["analysis"],
)

@router.get("/aep/example")
def run_example_aep():
    # Load example La Haute Borne dataset
    data_path = os.path.join("examples", "data", "la_haute_borne")
    
    # This prepares the data, extracting the zip file if necessary
    plant = project_ENGIE.prepare(path=data_path, return_value="plantdata")
    
    # Initialize AEP Analysis
    pa = MonteCarloAEP(
        plant, 
        reanalysis_products=["era5", "merra2"],
        time_resolution="ME",
        reg_model="lin",
        reg_temperature=False,
        reg_wind_direction=False,
    )
    
    # Run the Monte Carlo simulation with a lower number of simulations for API speed
    pa.run(num_sim=10, progress_bar=False)
    
    # Aggregate and return the results
    mean_results = pa.results.mean().to_dict()
    std_results = pa.results.std().to_dict()
    
    return {
        "status": "success",
        "message": "Monte Carlo AEP Analysis completed using La Haute Borne example data.",
        "simulations_run": 10,
        "results_mean": mean_results,
        "results_std": std_results
    }
