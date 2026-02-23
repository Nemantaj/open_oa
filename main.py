from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import openoa

from api import utils, analysis

app = FastAPI(title="OpenOA API")

app.include_router(utils.router)
app.include_router(analysis.router)
@app.get("/")
def read_root():
    return JSONResponse(content={"status": "OpenOA API is running on GCP Cloud Run", "version": openoa.__version__})

@app.get("/api/info")
def get_info():
    return JSONResponse(content={
        "message": "Welcome to the OpenOA GCP Serverless deployment.",
        "environment": "This is running inside a Docker container on Google Cloud Run.",
        "version": openoa.__version__
    })

if __name__ == "__main__":
    import uvicorn
    # Cloud Run injects the PORT environment variable
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
