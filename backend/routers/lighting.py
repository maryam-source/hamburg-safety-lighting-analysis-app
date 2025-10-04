# backend/routers/lighting.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from backend.models.lighting import PolygonInput
from backend.utils.geometry import validate_polygon
from backend.services.vector_service import compute_vector_stats
from backend.services.raster_service import compute_raster_stats
from backend.services.export_service import generate_csv
from backend.config import RASTER_PATH, DATA_DIR
from backend.services.data_loader import get_vector_grid
import pandas as pd
import rasterio
from rasterio.warp import transform_bounds
import rasterio.windows
import numpy as np
from PIL import Image
import morecantile
import mapbox_vector_tile
from io import BytesIO

router = APIRouter()

# Cached vector grid in EPSG:4326
vector_grid_4326 = get_vector_grid(crs="EPSG:4326")



# Stats endpoint
@router.post("/stats")
def lighting_stats(
    polygon_input: PolygonInput,
    return_values: bool = Query(False),
    return_histogram: bool = Query(False),
    nbins: int = Query(30),
):
    try:
        polygon = validate_polygon(polygon_input.geojson)
        vector_stats = compute_vector_stats(polygon, return_values)
        raster_stats = compute_raster_stats(polygon, return_histogram, nbins)
        return {"vector_stats": vector_stats, "raster_stats": raster_stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {e}")



# Export endpoint
@router.post("/export")
def lighting_export(
    polygon_input: PolygonInput,
    return_values: bool = Query(False),
    return_histogram: bool = Query(False),
    nbins: int = Query(30),
):
    try:
        polygon = validate_polygon(polygon_input.geojson)
        vector_stats = compute_vector_stats(polygon, return_values)
        raster_stats = compute_raster_stats(polygon, return_histogram, nbins)
        return generate_csv(vector_stats, raster_stats, return_values, return_histogram)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {e}")



# Raster tile endpoint
@router.get("/tiles/{z}/{x}/{y}.png")
def get_raster_tile(z: int, x: int, y: int):
    try:
        with rasterio.open(RASTER_PATH) as src:
            tms = morecantile.tms.get("WebMercatorQuad")
            tile_bounds_3857 = tms.bounds(x, y, z)

            left, bottom, right, top = transform_bounds(
                "EPSG:3857", src.crs,
                tile_bounds_3857.left, tile_bounds_3857.bottom,
                tile_bounds_3857.right, tile_bounds_3857.top,
                densify_pts=21
            )

            left = max(left, src.bounds.left)
            right = min(right, src.bounds.right)
            bottom = max(bottom, src.bounds.bottom)
            top = min(top, src.bounds.top)

            if left >= right or bottom >= top:
                data = np.zeros((256, 256), dtype=np.uint8)
            else:
                window = rasterio.windows.from_bounds(left, bottom, right, top, transform=src.transform)
                data = src.read(1, window=window, out_shape=(256, 256))
                data = np.nan_to_num(data, nan=0)
                if data.max() > data.min():
                    data = ((data - data.min()) / (data.max() - data.min()) * 255).astype(np.uint8)
                else:
                    data = np.zeros_like(data, dtype=np.uint8)

            img = Image.fromarray(data)
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print(f"[Raster Tile] Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Raster tile error: {e}")



# Vector tile endpoint
@router.get("/vector/tiles/{z}/{x}/{y}.pbf")
def get_vector_tile(z: int, x: int, y: int):
    try:
        tms = morecantile.tms.get("WebMercatorQuad")
        bounds = tms.bounds(x, y, z)

        minx, miny, maxx, maxy = bounds.left, bounds.bottom, bounds.right, bounds.top
        tile_gdf = vector_grid_4326.cx[minx:maxx, miny:maxy]

        features = []
        if not tile_gdf.empty:
            for _, row in tile_gdf.iterrows():
                features.append({
                    "geometry": row.geometry.__geo_interface__,
                    "properties": {"mean": float(row.mean_intensity), "name": getattr(row, "name", "lamp")}
                })

        layer = {"name": "grid_layer", "features": features}
        tile_pbf = mapbox_vector_tile.encode([layer])
        return StreamingResponse(content=tile_pbf, media_type="application/x-protobuf")

    except Exception as e:
        print(f"[Vector Tile] Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Vector tile error: {e}")



# Heatmap / Lamp points endpoint (not implemented in frontend for now)
@router.get("/lamps")
def get_lamps():
    try:
        lamp_csv_path = f"{DATA_DIR}/lighting_histogram.csv"
        df = pd.read_csv(lamp_csv_path)

        # Only include points if CSV has coordinates
        features = []
        if "lat" in df.columns and "lon" in df.columns:
            for _, row in df.iterrows():
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [float(row["lon"]), float(row["lat"])]},
                    "properties": {"intensity": float(row.get("intensity", 1.0))}
                })

        return {"type": "FeatureCollection", "features": features}

    except Exception as e:
        print(f"[Lamps] Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Lamp data error: {e}")
