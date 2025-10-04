# backend/services/vector_service.py
import geopandas as gpd
from shapely.ops import transform
import pyproj
import traceback
from fastapi import HTTPException

from backend.config import VECTOR_PATH

# Load vector grid once at startup
try:
    vector_grid = gpd.read_file(VECTOR_PATH)
    if "mean_intensity" not in vector_grid.columns:
        vector_grid["mean_intensity"] = 0.0
    print(f"[Vector Service] Loaded vector grid with {len(vector_grid)} features")
except Exception as e:
    print(f"[Vector Service] Failed to load vector grid: {e}")
    vector_grid = gpd.GeoDataFrame(columns=["geometry", "mean_intensity"], crs="EPSG:4326")


# Prepare transformer from WGS84 (EPSG:4326) to vector grid CRS
vector_crs = vector_grid.crs
project_to_vector_crs = pyproj.Transformer.from_crs(
    "EPSG:4326", vector_crs, always_xy=True
).transform


def compute_vector_stats(polygon, return_values: bool = False) -> dict:
   
    try:
        # Transform polygon to vector grid CRS
        polygon_in_grid_crs = transform(project_to_vector_crs, polygon)

        # Select intersecting features
        try:
            intersecting_gdf = gpd.clip(vector_grid, polygon_in_grid_crs)
        except Exception as e:
            # fallback if clip fails
            intersecting_gdf = vector_grid[vector_grid.intersects(polygon_in_grid_crs)]

        if intersecting_gdf.empty:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "count": 0, "values": None}

        # Ensure 'mean_intensity' column exists
        if "mean_intensity" not in intersecting_gdf.columns:
            intersecting_gdf["mean_intensity"] = 0.0

        # Compute statistics
        stats = {
            "mean": float(intersecting_gdf["mean_intensity"].mean()),
            "min": float(intersecting_gdf["mean_intensity"].min()),
            "max": float(intersecting_gdf["mean_intensity"].max()),
            "count": int(len(intersecting_gdf)),
            "values": intersecting_gdf["mean_intensity"].tolist() if return_values else None,
        }

        return stats

    except Exception as e:
        print("=== VECTOR SERVICE ERROR ===")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Vector stats computation error: {e}")


def reload_vector_grid():
    global vector_grid, vector_crs, project_to_vector_crs
    try:
        vector_grid = gpd.read_file(VECTOR_PATH)
        if "mean_intensity" not in vector_grid.columns:
            vector_grid["mean_intensity"] = 0.0
        vector_crs = vector_grid.crs
        project_to_vector_crs = pyproj.Transformer.from_crs(
            "EPSG:4326", vector_crs, always_xy=True
        ).transform
        print("[Vector Service] Vector grid reloaded successfully.")
        return vector_grid
    except Exception as e:
        print(f"[Vector Service] Failed to reload vector grid: {e}")
        traceback.print_exc()
        return None
