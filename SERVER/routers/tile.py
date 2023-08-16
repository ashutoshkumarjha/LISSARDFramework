from fastapi import APIRouter
import time
from osgeo import ogr, osr
from starlette.responses import StreamingResponse
from db import Db
import json
from sindexing import get_tile_intersection
from utils import tilenum2deg, get_tile_geom
from render import render_png, image_to_byte_array, render_png_multits, render_png_multits_o, render_png_multits_pre
from retrieval import load_data_refs, merge_tiles_tmp, merge_tiles, do_ndi, do_avg, scale_data, do_dif

router = APIRouter()


@router.get("/tile/{sensorName}/{z}/{x}/{y}.png")
def get_tile(
    tIndex: int,
    z: int,
    x: int,
    y: int,
    sensorName: str,
    bands: str = None,
    vmin: float = 0,
    vmax: float = 0.75,
    aoi_code: str = "uTUYvVGHgcvchgxc",
):
    try:
        dataset_def = Db.get_db_dataset_def_by_name(sensorName)
        aoi_value = Db.get_aoi_geom_by_aoi_code(aoi_code)
        start_time = time.time()
        gj = aoi_value["geom"]
        aoi_geom = ogr.CreateGeometryFromJson(gj)
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)
        aoi_geom.AssignSpatialReference(target_srs)
        bbox = tilenum2deg(x, y, z)
        tile_geom = get_tile_geom(x, y, z)
        if tile_geom.Intersects(aoi_geom) is False:
            return None
        level = z
        if level > 9:
            level = 9
        if level < 4:
            level = 4
        tiles = get_tile_intersection(level, [bbox[0], bbox[3], bbox[2], bbox[1]])
        if tiles is None:
            print("Failed to read sIndex")
            return None

        img = render_png(
            tiles, tIndex, sensorName, bbox, aoi_geom, bands, dataset_def, vmax
        )
        print("--- %s seconds ---" % (time.time() - start_time))
        if img is None:
            print("Failed to render")
            return img
        return StreamingResponse(image_to_byte_array(img), media_type="image/png")
    except Exception as e:
        print(e)
        print("Failed due to exception")
        return None


@router.get("/tilem/{sensorName}/{z}/{x}/{y}.png")
def get_tile_multi(
    tIndexes: str,
    z: int,
    x: int,
    y: int,
    sensorName: str,
    bands: str,
    vmin: float,
    vmax: float,
    aoi_code: str = "aoi_kedarnath",
):
    try:
        start_time = time.time()
        tIndexes = [int(v) for v in tIndexes.split(",")]
        dataset_def = Db.get_db_dataset_def_by_name(sensorName)
        print("DB1: %ss" % (round(time.time() - start_time, 3)))
        aoi_value = Db.get_aoi_geom_by_aoi_code(aoi_code)
        print("DB2: %ss" % (round(time.time() - start_time, 3)))
        gj = aoi_value["geom"]
        aoi_geom = ogr.CreateGeometryFromJson(gj)
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)
        aoi_geom.AssignSpatialReference(target_srs)
        bbox = tilenum2deg(x, y, z)
        tile_geom = get_tile_geom(x, y, z)
        if tile_geom.Intersects(aoi_geom) is False:
            return None
        level = z - 1
        if level > 11:
            level = 11
        if level < 4:
            level = 4
        tiles = get_tile_intersection(level, [bbox[0], bbox[3], bbox[2], bbox[1]])
        if tiles is None:
            print("Failed to read sIndex")
            return None
        print("SIndex: %ss" % (round(time.time() - start_time, 3)))

        img = render_png_multits(
            tiles, tIndexes, sensorName, bbox, aoi_geom, bands, dataset_def, vmax, vmin
        )
        print("RENDER: %ss" % (round(time.time() - start_time, 3)))
        # print("--- %s seconds ---" % (time.time() - start_time))
        if img is None:
            print("Failed to render")
            return img
        return StreamingResponse(image_to_byte_array(img), media_type="image/png")
    except Exception as e:
        print(e)
        # raise e
        print("Failed due to exception")
        return None


@router.get("/tilemo/{outputName}/{z}/{x}/{y}.png")
def get_tile_multio(
    z: int,
    x: int,
    y: int,
    outputName: str,
    vmin: float = 0,
    vmax: float = 1,
):
    try:
        bands = "4,3,2"
        result = Db.get_time_indexes_for_ds_aoi_out(
            outputName
        )
        tIndexes = [i['time_index'] for i in result]
        if len(tIndexes) > 10:
            return None
        print(tIndexes)
        start_time = time.time()
        print("DB1: %ss" % (round(time.time() - start_time, 3)))
        # aoi_value = Db.get_aoi_geom_by_aoi_code(aoi_code)
        # print("DB2: %ss" % (round(time.time() - start_time, 3)))
        # gj = aoi_value["geom"]
        # aoi_geom = ogr.CreateGeometryFromJson(gj)
        # target_srs = osr.SpatialReference()
        # target_srs.ImportFromEPSG(4326)
        # aoi_geom.AssignSpatialReference(target_srs)
        bbox = tilenum2deg(x, y, z)
        # tile_geom = get_tile_geom(x, y, z)
        # if tile_geom.Intersects(aoi_geom) is False:
        #     return None
        level = z - 1
        if level > 11:
            level = 11
        if level < 4:
            level = 4
        tiles = get_tile_intersection(level, [bbox[0], bbox[3], bbox[2], bbox[1]])
        if tiles is None:
            print("Failed to read sIndex")
            return None
        print("SIndex: %ss" % (round(time.time() - start_time, 3)))
        # print(tiles, tIndexes, outputName, bbox, aoi_geom, bands, vmax, vmin)

        img = render_png_multits_o(
            tiles, tIndexes, outputName, bbox, bands, vmax, vmin
        )
        print("RENDER: %ss" % (round(time.time() - start_time, 3)))
        # print("--- %s seconds ---" % (time.time() - start_time))
        if img is None:
            print("Failed to render")
            return img
        return StreamingResponse(image_to_byte_array(img), media_type="image/png")
    except Exception as e:
        print(e)
        # raise e
        print("Failed due to exception")
        return None
        
def perform_ndi(inds, b1, b2, projWin):
    ds = merge_tiles(inds["ds"], projWin)
    ds = do_ndi(ds, b1, b2)
    return {"ds": [ds], "ts": inds['ts']}

def perform_mosaic(inds, projWin, pidx, dataset_def):
    ds = merge_tiles(inds["ds"], projWin)
    if(pidx==0):
        ds = scale_data(ds, dataset_def)
    return {"ds": [ds], "ts": inds['ts']}

def perform_avg(inds1, inds2, projWin, pidx, dataset_def):
    ds1 = merge_tiles(inds1["ds"], projWin)
    ds2 = merge_tiles(inds2["ds"], projWin)
    ds = do_avg(ds1, ds2)
    if(pidx==0):
        ds = scale_data(ds, dataset_def)
    return {"ds": [ds], "ts": inds1['ts']}

def perform_dif(inds1, inds2, projWin, pidx, dataset_def):
    ds1 = merge_tiles(inds1["ds"], projWin)
    ds2 = merge_tiles(inds2["ds"], projWin)
    ds = do_dif(ds1, ds2)
    if(pidx==0):
        ds = scale_data(ds, dataset_def)
    return {"ds": [ds], "ts": inds1['ts']}
    

@router.get("/tilepro/{taskName}/{z}/{x}/{y}.png")
def get_tile_preview(
    z: int,
    x: int,
    y: int,
    taskName: str,
    bands: str,
    vmin: float,
    vmax: float,
    aoi_code: str = "AVSQFSNWOYLMNOQG",
):
    # try:
        # /tilepro/ZZGIHWNUJOKEMPET/8/184/105.png?bands=1&vmin=0&vmax=1
        task_data = Db.get_task_preview_by_tid(taskName)
        task_data = json.loads(task_data['task_data'])
        # print(task_data)
        # task_data = {"inputs":[{"id":"kb625q","tIndexes":[859267663,858404194,857972449,859267683,858835939,857972429,857972409,858404174,859267643,858835919,858404154],"isTemporal":True,"aoiCode":"AVSQFSNWOYLMNOQG","dsName":"LISS3"}],"operations":[{"id":"ct54iw","type":"op_ndi","inputs":[{"id":"kb625q","band":0}],"output":{"id":"6ogc84"},"params":"kb625q:2#kb625q:1"}],"output":{"id":"6ogc84"}}
        aoi_code = task_data['inputs'][0]['aoiCode']
        start_time = time.time()
        ds_id = task_data['inputs'][0]['dsName']
        dataset_def = Db.get_db_dataset_def_by_name(ds_id)
        # return null
        print("DB1: %ss" % (round(time.time() - start_time, 3)))
        aoi_value = Db.get_aoi_geom_by_aoi_code(aoi_code)
        print("DB2: %ss" % (round(time.time() - start_time, 3)))
        gj = aoi_value["geom"]
        aoi_geom = ogr.CreateGeometryFromJson(gj)
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(4326)
        aoi_geom.AssignSpatialReference(target_srs)
        bbox = tilenum2deg(x, y, z)
        tile_geom = get_tile_geom(x, y, z)
        if tile_geom.Intersects(aoi_geom) is False:
            return None
        level = z - 1
        if level > 11:
            level = 11
        if level < 4:
            level = 4
        tiles = [[int(t) for t in tile.split('#')] for tile in get_tile_intersection(level, [bbox[0], bbox[3], bbox[2], bbox[1]])]
        if tiles is None:
            print("Failed to read sIndex")
            return None
        print("SIndex: %ss" % (round(time.time() - start_time, 3)))

        #prepare inputs
        indatas = {}
        for inp in task_data['inputs']:
            #{"id":"kb625q","tIndexes":[859267663,858404194,857972449,859267683,858835939,857972429,857972409,858404174,859267643,858835919,858404154],"isTemporal":True,"aoiCode":"AVSQFSNWOYLMNOQG","dsName":"LISS3"}
            tindexes = inp['tIndexes']
            in_ds = load_data_refs(tiles, tindexes, dataset_def['dataset_id'], level) #[ for tindex in tindexes]
            indatas[inp['id']] = {"ds": in_ds, "ts": tindexes[0]}
        # print(indatas)

        # do preview process
        pidx = 0
        for procs in task_data['operations']:
            # print(procs)
            if procs['type'] == 'op_ndi':
                in1 = indatas[procs["inputs"][0]["id"]]
                b1 = int(procs["params"].split('#')[0].split(':')[1])
                b2 = int(procs["params"].split('#')[1].split(':')[1])
                ods = perform_ndi(in1, b1, b2, bbox)
                indatas[procs["output"]["id"]] = ods
            
            if procs['type'] == 'op_mosaic_full':
                in1 = indatas[procs["inputs"][0]["id"]]
                ods = perform_mosaic(in1, bbox, pidx, dataset_def)
                indatas[procs["output"]["id"]] = ods
            
            if procs['type'] == 'op_local_avg':
                in1 = indatas[procs["inputs"][0]["id"]]
                in2 = indatas[procs["inputs"][1]["id"]]
                ods = perform_avg(in1, in2, bbox, pidx, dataset_def)
                indatas[procs["output"]["id"]] = ods
            
            if procs['type'] == 'op_local_dif':
                in1 = indatas[procs["inputs"][0]["id"]]
                in2 = indatas[procs["inputs"][1]["id"]]
                ods = perform_dif(in1, in2, bbox, pidx, dataset_def)
                indatas[procs["output"]["id"]] = ods
            
            pidx += 1
        
        out_ds = indatas[task_data["output"]["id"]]['ds']
        print(out_ds)
        # return None

        img = render_png_multits_pre(
            out_ds, bbox, aoi_geom, bands, dataset_def, vmax, vmin
        )
        print("RENDER: %ss" % (round(time.time() - start_time, 3)))
        # print("--- %s seconds ---" % (time.time() - start_time))
        if img is None:
            print("Failed to render")
            return img
        return StreamingResponse(image_to_byte_array(img), media_type="image/png")
    # except Exception as e:
    #     print(e)
    #     # raise e
    #     print("Failed due to exception")
    #     return None