# backend/services/data_loader.py
import geopandas as gpd
import rasterio
import numpy as np
from rasterio.io import DatasetReader
from backend.config import VECTOR_PATH, RASTER_PATH
from pyproj import CRS

# GLOBAL VARIABLES
vector_grid: gpd.GeoDataFrame = None
vector_grid_4326: gpd.GeoDataFrame = None  # cached WGS84 copy for MVT / bbox queries
raster_src: DatasetReader = None
raster_data: np.ndarray = None
raster_min: float = None
raster_max: float = None
raster_crs: CRS = None
raster_bounds = None
raster_shape = None

# LOAD VECTOR GRID
def load_vector_grid(force_reload: bool = False):
    """
    Load the vector grid GeoPackage and cache a WGS84 copy for vector tile requests.
    """
    global vector_grid, vector_grid_4326
    if vector_grid is not None and not force_reload:
        return vector_grid

    try:
        vector_grid = gpd.read_file(VECTOR_PATH)

        # Ensure required columns exist
        if "name" not in vector_grid.columns:
            vector_grid["name"] = "lamp"
        if "mean_intensity" not in vector_grid.columns:
            vector_grid["mean_intensity"] = 0.0

        # Cache EPSG:4326 copy for MVT / bbox queries
        vector_grid_4326 = vector_grid.to_crs("EPSG:4326")
        print(f"[Data Loader] Vector grid loaded: {len(vector_grid)} features, CRS={vector_grid.crs}")
        return vector_grid
    except Exception as e:
        raise RuntimeError(f"[Data Loader] Failed to load vector grid: {VECTOR_PATH}\n{e}")


# LOAD RASTER
def load_raster(force_reload: bool = False):
    """
    Load the high-resolution raster (COG) for analysis.
    """
    global raster_src, raster_data, raster_min, raster_max, raster_crs, raster_bounds, raster_shape
    if raster_src is not None and not force_reload:
        return raster_src

    try:
        raster_src = rasterio.open(RASTER_PATH)
        raster_data = raster_src.read(1, masked=True)

        # Compute min/max robustly
        masked_data = np.ma.filled(raster_data, np.nan)
        raster_min = float(np.nanmin(masked_data))
        raster_max = float(np.nanmax(masked_data))

        raster_crs = raster_src.crs
        raster_bounds = raster_src.bounds
        raster_shape = raster_data.shape

        print(f"[Data Loader] Raster loaded: shape={raster_shape}, CRS={raster_crs}, min={raster_min}, max={raster_max}")
        return raster_src
    except Exception as e:
        raise RuntimeError(f"[Data Loader] Failed to load raster: {RASTER_PATH}\n{e}")


# INITIAL LOAD (optional)
try:
    load_vector_grid()
except Exception as e:
    print(f"[Data Loader] Vector grid not loaded on startup: {e}")

try:
    load_raster()
except Exception as e:
    print(f"[Data Loader] Raster not loaded on startup: {e}")


# UTILITY FUNCTIONS
def get_raster_metadata():
    """Return basic metadata of the raster."""
    return {
        "crs": str(raster_crs),
        "bounds": raster_bounds,
        "shape": raster_shape,
        "min": raster_min,
        "max": raster_max,
    }

def get_vector_grid(crs="original"):
    """
    Return the vector grid. Optionally return in EPSG:4326 (for MVT / bbox queries).
    """
    if crs == "EPSG:4326":
        return vector_grid_4326
    return vector_grid

def reload_vector_grid():
    """Reload the vector grid from file and update cached WGS84 copy."""
    return load_vector_grid(force_reload=True)

def reload_raster():
    """Reload the raster from file."""
    return load_raster(force_reload=True)
