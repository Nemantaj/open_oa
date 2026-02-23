# Dockerfile for GCP Cloud Run Deployment
# Use a standard Python slim image
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
WORKDIR $APP_HOME

# Install system dependencies (needed for compiling some python packages like pandas, scipy, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy local code to the container image
COPY . ./

# Install project dependencies
# This uses the pyproject.toml to install openoa and its dependencies
RUN pip install --no-cache-dir .

# Install the API server dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the web service on container startup using uvicorn.
# Cloud Run automatically injects the PORT environment variable (default 8080).
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
