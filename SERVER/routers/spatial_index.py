from fastapi import APIRouter
from ingestion import partition_data
from pydantic import BaseModel
from sindexing import generate_index, get_tile_intersection

router = APIRouter()

class GenerateSIndex(BaseModel):
    shapefile_path: str

@router.post("/generateSpatialIndex")
async def generate_spatial_index(index_request: GenerateSIndex):
    try:
        generate_index(
            index_request.shapefile_path
        )
        return {
            "error": False,
            "message": "Spatial Index Generated"
        }
    except Exception as e:
        print(e)
        return {
            "error": True,
            "message": "Error"
        }

@router.get("/getSpatialIndex/{level}")
def get_spatial_index(level: int, xmin: float, xmax: float, ymin: float, ymax: float):
    results = get_tile_intersection(level, [xmin, ymin, xmax, ymax]) #[n.object for n in index_dat[level].intersection([xmin, ymin, xmax, ymax], objects=True)]
    return {
        "error": False,
        "message": "Success",
        "data": results
    }