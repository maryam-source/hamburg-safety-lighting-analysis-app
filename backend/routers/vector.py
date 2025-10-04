# routers/vector.py
import json
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from shapely.geometry import box, mapping
from shapely import ops
import mapbox_vector_tile
from pyproj import Transformer
import mercantile

from backend.services.data_loader import get_vector_grid  # use getter to access current vector grid

router = APIRouter()

# Vector GeoJSON endpoint
@router.get("")
def get_vector(
    bbox: str = Query(None),
    full: bool = Query(False),
):
    """
    Return vector features as GeoJSON.
    Provide bbox=minx,miny,maxx,maxy or set full=True to get all features.
    """
    try:
        # EPSG:4326 copy for bbox queries
        grid = get_vector_grid(crs="EPSG:4326")

        if bbox:
            parts = bbox.split(",")
            if len(parts) != 4:
                raise HTTPException(status_code=400, detail="bbox must be minx,miny,maxx,maxy")
            minx, miny, maxx, maxy = map(float, parts)
            geom = box(minx, miny, maxx, maxy)
            sel = grid[grid.intersects(geom)]
        elif full:
            sel = grid
        else:
            raise HTTPException(status_code=400, detail="Must provide bbox or set full=True")

        return json.loads(sel.to_json())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector endpoint error: {e}")

# Vector tile endpoint (MVT)
@router.get("/tiles/{z}/{x}/{y}.pbf")
def vector_tile(z: int, x: int, y: int):
    """
    Return Mapbox Vector Tile (MVT) for the given XYZ tile.
    """
    try:
        # Compute tile bounds in WGS84
        tile = mercantile.Tile(x=x, y=y, z=z)
        bounds = mercantile.bounds(tile)  # west, south, east, north
        tile_geom = box(bounds.west, bounds.south, bounds.east, bounds.north)

        # Filter features intersecting tile in EPSG:4326
        grid = get_vector_grid(crs="EPSG:4326")
        sel = grid[grid.intersects(tile_geom)].copy()

        # Keep only non-zero intensity cells
        if "mean_intensity" in sel.columns:
            sel = sel[sel["mean_intensity"] > 0]

        if sel.empty:
            empty_tile = mapbox_vector_tile.encode({"grid": []})
            return Response(empty_tile, media_type="application/x-protobuf")

        # Transform geometries to WebMercator (EPSG:3857) for tile encoding
        transformer = Transformer.from_crs(sel.crs, "EPSG:3857", always_xy=True)
        features = []
        for _, row in sel.iterrows():
            geom_3857 = ops.transform(transformer.transform, row.geometry)
            feature = {
                "geometry": mapping(geom_3857),
                "properties": {
                    "mean_intensity": float(row["mean_intensity"])
                }
            }
            features.append(feature)

        # Encode as MVT
        tile_data = mapbox_vector_tile.encode({"grid": features})

        return Response(tile_data, media_type="application/x-protobuf")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector tile error: {e}")
