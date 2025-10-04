# backend/routers/vector_tiles.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from shapely.geometry import box, mapping
from shapely import ops
from pyproj import Transformer
import mapbox_vector_tile
from backend.services.data_loader import get_vector_grid
from math import atan, exp, pi

router = APIRouter()

# Load vector grid once at startup
grid = get_vector_grid(crs="EPSG:4326")  # WGS84

# Transformer to Web Mercator
transformer_to_3857 = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

# Helper: convert z/x/y tile to bbox in EPSG:4326
def tile_bounds(x: int, y: int, z: int):
    n = 2.0 ** z
    lon_min = x / n * 360.0 - 180.0
    lon_max = (x + 1) / n * 360.0 - 180.0
    lat_min = (180.0 / pi) * (2.0 * atan(exp(pi * (1 - 2 * (y + 1) / n))) - pi/2)
    lat_max = (180.0 / pi) * (2.0 * atan(exp(pi * (1 - 2 * y / n))) - pi/2)
    return (lon_min, lat_min, lon_max, lat_max)

# Vector tile endpoint
@router.get("/tiles/{z}/{x}/{y}.pbf")
def get_tile(z: int, x: int, y: int):
    try:
        # compute tile bbox
        minx, miny, maxx, maxy = tile_bounds(x, y, z)
        tile_geom = box(minx, miny, maxx, maxy)

        # select intersecting features
        sel = grid[grid.intersects(tile_geom)]

        # if no features, return empty MVT tile
        if sel.empty:
            empty_layer = {"name": "grid_layer", "features": []}
            tile_data = mapbox_vector_tile.encode([empty_layer])
            return Response(content=tile_data, media_type="application/x-protobuf")

        # transform geometries to Web Mercator
        features = []
        for _, row in sel.iterrows():
            geom_3857 = ops.transform(transformer_to_3857.transform, row.geometry)
            features.append({
                "geometry": mapping(geom_3857),
                "properties": {
                    "mean": float(row.mean_intensity),
                    "name": row.name if "name" in row else "lamp"
                }
            })

        # encode as MVT
        layer = {"name": "grid_layer", "features": features}
        tile_data = mapbox_vector_tile.encode([layer])

        return Response(content=tile_data, media_type="application/x-protobuf")

    except Exception as e:
        print(f"[Vector Tile] Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Vector tile error: {e}")
