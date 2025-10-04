# routers/metadata.py
import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from backend.config import METADATA_PATH  # absolute import

router = APIRouter()

# Metadata endpoint
@router.get("")
def get_metadata():
    """
    Return the lighting metadata as JSON.
    """
    if not os.path.exists(METADATA_PATH):
        raise HTTPException(status_code=404, detail="Metadata file not found")

    try:
        with open(METADATA_PATH, "r") as f:
            meta = json.load(f)
        return JSONResponse(content=meta)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to decode metadata JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading metadata: {e}")
