from fastapi import APIRouter
from ingestion import partition_data

router = APIRouter()

@router.get("/ingestData")
def ingest_data(filePath: str, sensorName: str, ts: int):
    try:
        result = partition_data(filePath, ts, sensorName)
        return {
            "error": False,
            "message": "Success",
            "data": result
        }
    except Exception as e:
        print(e)
        return {
            "error": True,
            "message": "Exception",
            "data": None
        }