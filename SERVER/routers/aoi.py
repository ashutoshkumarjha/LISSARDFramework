from fastapi import APIRouter
from db import Db
from pydantic import BaseModel

class AddAoiReq(BaseModel):
    aoiGj: str
    aoiName: str

router = APIRouter()

@router.get("/getAois")
def get_aois():
    try:
        aois = Db.get_db_all_aoi_names()
        return {
            "error": False,
            "message": "Success",
            "data": aois
        }
    except Exception as e:
        print(e)
        return {
            "error": True,
            "message": "Exception",
            "data": None
        }

@router.get("/getAoiByCode")
def get_aoi_by_code(aoiCode: str):
    try:
        aoi = Db.get_aoi_geom_by_aoi_code(aoiCode)
        return {
            "error": False,
            "message": "Success",
            "data": aoi
        }
    except Exception as e:
        print(e)
        return {
            "error": True,
            "message": "Exception",
            "data": None
        }
    

@router.post("/addAoi")
def add_aoi(req: AddAoiReq):
    try:
        aoi = Db.insert_aoi(req.aoiName, req.aoiGj)
        return {
            "error": False,
            "message": "Success",
            "data": aoi
        }
    except Exception as e:
        print(e)
        return {
            "error": True,
            "message": "Exception",
            "data": None
        }