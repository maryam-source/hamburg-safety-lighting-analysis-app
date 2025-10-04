# backend/services/export_service.py
import io
import csv
from fastapi.responses import StreamingResponse

def generate_csv(
    vector_stats: dict,
    raster_stats: dict,
    return_values: bool = False,
    return_histogram: bool = False,
) -> StreamingResponse:
  
    output = io.StringIO()
    writer = csv.writer(output)

    # Vector statistics
    writer.writerow(["Vector Statistics", "Value"])
    writer.writerow(["Mean", vector_stats.get("mean", 0)])
    writer.writerow(["Min", vector_stats.get("min", 0)])
    writer.writerow(["Max", vector_stats.get("max", 0)])
    writer.writerow(["Count", vector_stats.get("count", 0)])
    writer.writerow([])

    # Raster statistics
    writer.writerow(["Raster Statistics", "Value"])
    writer.writerow(["Mean", raster_stats.get("mean", 0)])
    writer.writerow(["Min", raster_stats.get("min", 0)])
    writer.writerow(["Max", raster_stats.get("max", 0)])
    writer.writerow([])

    # Optional: raw vector values
    if return_values and vector_stats.get("values"):
        writer.writerow(["Vector Values"])
        for val in vector_stats["values"]:
            writer.writerow([val])
        writer.writerow([])

  
    # Optional: raster histogram
    if return_histogram and raster_stats.get("histogram"):
        hist = raster_stats["histogram"]
        writer.writerow(["Histogram Start", "Histogram End", "Count"])
        for start, end, count in zip(hist["bins_start"], hist["bins_end"], hist["counts"]):
            writer.writerow([start, end, count])

  
    # Prepare CSV for streaming response
    output.seek(0)
    csv_data = output.getvalue()
    output.close()

    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=lighting_stats.csv"},
    )
