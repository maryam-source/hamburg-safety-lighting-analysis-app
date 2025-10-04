import geopandas as gpd
import rasterio
from shapely.geometry import box

# load vector grid
vector_file = "data/lighting_vector_grid_nonzero.gpkg"
vector_grid = gpd.read_file(vector_file)

print("\nVector Grid CRS:", vector_grid.crs)
print("Vector Grid Bounds:", vector_grid.total_bounds)
print("Number of rows:", len(vector_grid))

# create test polygon
hamburg_bbox = [9.8, 53.45, 10.1, 53.65]  # approx Hamburg
test_poly = box(*hamburg_bbox)

# ensure CRS matches
if vector_grid.crs != "EPSG:4326":
    print("Reprojecting vector grid to EPSG:4326...")
    vector_grid = vector_grid.to_crs("EPSG:4326")

# test intersection
intersecting = vector_grid[vector_grid.intersects(test_poly)]
print("\nNumber of intersecting vector rows:", len(intersecting))
if len(intersecting) > 0:
    print("Sample row:")
    print(intersecting.iloc[0])

# check raster bounds
raster_file = "data/lighting_model_highres_disk.tif"
with rasterio.open(raster_file) as src:
    print("\nRaster CRS:", src.crs)
    print("Raster bounds:", src.bounds)
