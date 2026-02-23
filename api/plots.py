from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import matplotlib.pyplot as plt
import matplotlib
import io

# Setup matplotlib for non-gui backend so server doesn't crash
matplotlib.use('Agg')

from .data import datasets_store
from openoa.utils import plot

router = APIRouter(
    prefix="/api/plots",
    tags=["plots"],
)

@router.get("/power-curve/{dataset_id}")
def get_power_curve_plot(dataset_id: str):
    if dataset_id not in datasets_store:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    plant = datasets_store[dataset_id]
    
    try:
        # Plot power curve. Need scatter plot of windspeed vs power
        # For simplicity, we just plot the 1st turbine's data in the scada frame
        turbine_ids = plant.scada[plant.metadata.scada.id].unique()
        df_sub = plant.scada[plant.scada[plant.metadata.scada.id] == turbine_ids[0]]
        
        ws = df_sub[plant.metadata.scada.windspeed]
        power = df_sub[plant.metadata.scada.power]
        
        fig, ax = plt.subplots(figsize=(8, 5))
        plot.plot_power_curve(ws, power, ax=ax, scatter_kwargs={"alpha": 0.2, "s": 2})
        ax.set_title(f"Power Curve - Turbine {turbine_ids[0]}")
        
        # Save to memory buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        plt.close(fig)
        buf.seek(0)
        
        return Response(content=buf.getvalue(), media_type="image/png")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
