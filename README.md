
# Lighting Intensity Web Application

This repository contains the practical implementation for the **Lighting Intensity Web Application**.  
The goal is to model **urban lighting intensity** from street lamp data and provide an **interactive web application** for spatial analysis.

---

# Overview

The app enables users to:
1. Visualize modeled lighting intensity (raster or vector data).
2. Draw custom polygons on the map.
3. Retrieve summary statistics (mean, min, max, distribution).
4. Export results as CSV.

The system combines a **FastAPI backend** (geospatial analysis) and a **simple JavaScript frontend** (Leaflet map).

---

# Setup Instructions

# Clone the repository

```bash
git clone https://github.com/maryam-source/lighting_app.git
cd lighting_app

# Activate your environment
conda activate lighting-env

# If you don’t already have this environment, create one:
conda create -n lighting-env python=3.10
conda activate lighting-env
pip install fastapi uvicorn geopandas rasterio shapely pydantic matplotlib

# Running the Application

# Backend (FastAPI)
cd /lighting_app
python -m uvicorn backend.main:app --reload --log-level debug

# This will start the API at http://127.0.0.1:8000
# You can explore the automatically generated documentation at: Interactive Docs: http://127.0.0.1:8000/docs Alternative view: http://127.0.0.1:8000/redoc

#Frontend (Static)
cd /lighting_app/frontend
python -m http.server 8080

# Then open your browser at: http://localhost:8080

# Project Structure

lighting_app/
├── backend/
│   ├── main.py                # FastAPI entrypoint
│   ├── routers/               # API endpoints
│   ├── services/              # Data access logic
│   ├── models/                # Pydantic schemas
│   ├── utils/                 # Geometry helpers
│   └── data/                  # Raster & vector inputs
│
├── frontend/
│   ├── index.html             # Map interface
│   ├── app.js                 # Polygon drawing + API calls
│   └── style.css
│
├── storage.ipynb              #exploratory notebook
├── TECHNICAL_DOCUMENTATION.md # Full write-up of architecture
├── LICENSE
└── .gitignore
