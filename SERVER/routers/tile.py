from fastapi import APIRouter
import time
from osgeo import ogr, osr
from starlette.responses import StreamingResponse
from db import Db
from sindexing import get_tile_intersection
from utils import tilenum2deg, get_tile_geom
from render import render_png, image_to_byte_array

router = APIRouter()

@router.get("/tile/{sensorName}/{z}/{x}/{y}.png")
def get_tile(tIndex: int, z: int, x: int, y: int, sensorName: str, bands: str = None, vmin: float = 0, vmax: float = 0.75, aoi_code: str = 'uTUYvVGHgcvchgxc'):
    try:
        dataset_def = Db.get_db_dataset_def_by_name(sensorName)
        aoi_value = Db.get_aoi_geom_by_aoi_code(aoi_code)
        start_time = time.time()
        gj = aoi_value['geom']
        aoi_geom = ogr.CreateGeometryFromJson(gj)
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)
        aoi_geom.AssignSpatialReference(target_srs)
        bbox = tilenum2deg(x, y, z)
        tile_geom = get_tile_geom(x, y, z)
        if(tile_geom.Intersects(aoi_geom) is False):
            return None
        level = z
        if(level > 12):
            level = 12
        if(level < 4):
            level = 4
        tiles = get_tile_intersection(level, [bbox[0], bbox[3], bbox[2], bbox[1]])
        if(tiles is None):
            print("Failed to read sIndex")
            return None
        
        img = render_png(tiles, tIndex, sensorName, bbox, aoi_geom, bands, dataset_def, vmax)
        print("--- %s seconds ---" % (time.time() - start_time))
        if(img is None):
            print("Failed to render")
            return img
        return StreamingResponse(image_to_byte_array(img), media_type="image/png")
    except Exception as e:
        print(e)
        print("Failed due to exception")
        return None
    