from fastapi.testclient import TestClient
from main import app
import pprint

client = TestClient(app)

print("Testing Utils Endpoint...")
try:
    response = client.post("/api/utils/air-density-adjusted-wind-speed", json={
        "wind_speeds": [10.0, 12.0],
        "air_densities": [1.1, 1.2]
    })
    print("Status code:", response.status_code)
    pprint.pprint(response.json())
except Exception as e:
    print("Error:", e)

print("\nTesting Analysis Endpoint...")
try:
    # Set timeout extremely high globally because analysis might take some time
    response = client.get("/api/analysis/aep/example")
    print("Status code:", response.status_code)
    pprint.pprint(response.json())
except Exception as e:
    print("Error:", e)
