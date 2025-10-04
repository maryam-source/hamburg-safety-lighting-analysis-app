# backend/utils/geometry.py
from fastapi import HTTPException
from shapely.geometry import shape, Polygon, MultiPolygon, mapping

def validate_polygon(geojson_dict):
    geom = None

    try:
        geo_type = geojson_dict.get("type")
        if geo_type == "Feature":
            geom = shape(geojson_dict.get("geometry", {}))
        elif geo_type == "FeatureCollection":
            features = geojson_dict.get("features", [])
            if not features:
                raise HTTPException(status_code=400, detail="FeatureCollection is empty")
            geom = shape(features[0].get("geometry", {}))
        elif geo_type in ["Polygon", "MultiPolygon"]:
            geom = shape(geojson_dict)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported GeoJSON type: {geo_type}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON: {e}")

    # Validate geometry type
    if not isinstance(geom, (Polygon, MultiPolygon)):
        raise HTTPException(status_code=400, detail="Geometry must be Polygon or MultiPolygon")

    return geom


def polygon_to_geojson(geom):
    if not isinstance(geom, (Polygon, MultiPolygon)):
        raise ValueError("Input must be a Polygon or MultiPolygon")
    return mapping(geom)
