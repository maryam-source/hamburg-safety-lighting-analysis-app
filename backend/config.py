# backend/config.py
import os


# Base directory of the backend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the data folder inside backend
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Paths to specific data files
# Vector grid (GeoPackage, fixed version to ensure reliable tiles)
VECTOR_PATH = os.path.join(DATA_DIR, "lighting_vector_grid_nonzero_fixed.gpkg")

# High-resolution raster (Cloud-Optimized GeoTIFF)
RASTER_PATH = os.path.join(DATA_DIR, "lighting_model_highres_disk_cog.tif")

# Histogram CSV (lamp intensity distribution)
HISTOGRAM_PATH = os.path.join(DATA_DIR, "lighting_histogram.csv")

# Raster metadata JSON (optional, for frontend / diagnostics)
METADATA_PATH = os.path.join(DATA_DIR, "lighting_metadata.json")

# Non-zero raster area vector (optional / debugging)
NONZERO_RASTER_PATH = os.path.join(DATA_DIR, "nonzero_raster_area.gpkg")

# Debug / logging flags
DEBUG = True

# Map / Tiles configuration
# Tile size in pixels
TILE_SIZE = 256

# Web Mercator CRS for map tiles
WEBMERCATOR_CRS = "EPSG:3857"

# Default vector grid CRS (WGS84)
VECTOR_CRS = "EPSG:4326"

# Optional: Tile server config
# Maximum zoom level for raster/vector tiles
MAX_ZOOM = 22

# Minimum zoom level for raster/vector tiles
MIN_ZOOM = 0
