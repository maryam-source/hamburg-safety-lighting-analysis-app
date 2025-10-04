# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Routers
from backend.routers import lighting, metadata, vector_tiles

# Config
from backend.config import DATA_DIR
from backend.services import data_loader  # Ensure datasets are loaded on startup

# Optional: TiTiler support for on-the-fly COG serving
try:
    from titiler.application import create_app as create_titiler_app
    HAS_TITILER = True
except ImportError:
    HAS_TITILER = False


# FASTAPI APP
app = FastAPI(title="Urban Lighting API", version="1.0")


# CORS Middleware (for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to your frontend domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (data folder)
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Optional: TiTiler app for COGs
if HAS_TITILER:
    app.mount("/titiler", create_titiler_app())


# Load vector and raster datasets on startup
@app.on_event("startup")
def load_datasets():
    """
    Load vector and raster data before serving requests to avoid 404 errors.
    """
    try:
        data_loader.load_vector_grid()
        data_loader.load_raster()
        print("[Startup] Vector and raster data loaded successfully.")
    except Exception as e:
        print(f"[Startup] Failed to load datasets: {e}")


# Register routers
app.include_router(lighting.router, prefix="/lighting", tags=["lighting"])
app.include_router(vector_tiles.router, prefix="/vector", tags=["vector"])
app.include_router(metadata.router, prefix="/metadata", tags=["metadata"])


# Root endpoint (health check)
@app.get("/")
def root():
    return {"message": "Urban Lighting API is running"}
