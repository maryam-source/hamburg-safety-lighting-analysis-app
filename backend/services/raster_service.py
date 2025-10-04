# backend/services/raster_service.py
import numpy as np
from rasterio.mask import mask
from shapely.ops import transform
import pyproj
import traceback

from backend.services.data_loader import raster_src, raster_min, raster_max

# Prepare transformer from WGS84 (EPSG:4326) to raster CRS
raster_crs = raster_src.crs
project_to_raster_crs = pyproj.Transformer.from_crs(
    "EPSG:4326", raster_crs, always_xy=True
).transform


def compute_raster_stats(polygon, return_histogram: bool = False, nbins: int = 30) -> dict:
    try:
        # Transform polygon to raster CRS
        polygon_in_raster_crs = transform(project_to_raster_crs, polygon)

        # Mask raster with polygon
        out_image, out_transform = mask(
            raster_src,
            [polygon_in_raster_crs.__geo_interface__],
            crop=True,
            filled=False
        )

        # Flatten and remove masked values
        data = out_image[0].compressed()
        if data.size == 0:
            return {"mean": 0.0, "min": 0.0, "max": 0.0, "histogram": None}

        # Compute basic stats
        stats = {
            "mean": float(np.nanmean(data)),
            "min": float(np.nanmin(data)),
            "max": float(np.nanmax(data)),
        }

        # Compute histogram if requested
        if return_histogram:
            bins = np.linspace(raster_min, raster_max, nbins + 1)
            counts, _ = np.histogram(data, bins=bins)
            stats["histogram"] = {
                "bins_start": bins[:-1].tolist(),
                "bins_end": bins[1:].tolist(),
                "counts": counts.tolist(),
            }

        return stats

    except Exception as e:
        print("=== RASTER SERVICE ERROR ===")
        traceback.print_exc()
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "histogram": None}


def reload_raster():
    global raster_src, raster_crs, project_to_raster_crs
    try:
        from backend.services.data_loader import reload_raster as dl_reload
        raster_src = dl_reload()
        raster_crs = raster_src.crs
        project_to_raster_crs = pyproj.Transformer.from_crs(
            "EPSG:4326", raster_crs, always_xy=True
        ).transform
        print("[Raster Service] Raster reloaded successfully.")
        return raster_src
    except Exception as e:
        print(f"[Raster Service] Failed to reload raster: {e}")
        traceback.print_exc()
        return None
