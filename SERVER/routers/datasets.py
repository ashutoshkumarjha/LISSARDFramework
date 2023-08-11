from fastapi import APIRouter
import datetime, time
import numpy as np
from osgeo import ogr, osr
from db import Db
from sindexing import get_tile_intersection
from retrieval import (
    load_data,
    merge_tiles,
    time_indexes_ts,
    ts_to_tindex,
    load_data_ref,
)

router = APIRouter()


@router.get("/getDatasets")
def get_datasets():
    try:
        ds = Db.get_db_all_dataset_def()
        return {"error": False, "message": "Success", "data": ds}
    except Exception as e:
        print(e)
        return {"error": True, "message": "Exception", "data": None}


@router.get("/getTimeIndexes")
def get_time_indexes(
    sensorName: str,
    fromTs: int = None,
    toTs: int = None,
    aoi_code: str = "uTUYvVGHgcvchgxc",
):
    try:
        ds_def = Db.get_db_dataset_def_by_name(sensorName)
        result = Db.get_time_indexes_for_ds_aoi(
            aoi_code, ds_def["dataset_id"], fromTs, toTs
        )
        data = []
        for t in result:
            data.append(
                {
                    "ts": int(datetime.datetime.timestamp(t["date_time"])) * 1000,
                    "tIndex": t["time_index"],
                    "dsName": ds_def["ds_name"],
                    "dsId": ds_def["dataset_id"],
                    "dsData": ds_def,
                    "aoiCode": aoi_code,
                }
            )
        return {"error": False, "message": "Success", "data": data}
    except Exception as e:
        print(e)
        return {"error": True, "message": "Exception", "data": None}


@router.get("/getDataForBbox/{level}")
def get_data_for_bbox(
    sensorName: str,
    level: int,
    tIndex: int,
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
):
    start_time = time.time()
    tindex = tIndex
    tiles = get_tile_intersection(
        level, [xmin, ymin, xmax, ymax]
    )  # [n.object for n in index_dat[level].intersection([xmin, ymin, xmax, ymax], objects=True)]
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    for tile in tiles:
        ds = load_data(tile, tindex, sensorName)
        merge_ds.append(ds)

    out_path = merge_tiles(merge_ds, [xmin, ymax, xmax, ymin])
    print("--- %s seconds ---" % (time.time() - start_time))
    return {"error": False, "message": "Success", "data": out_path}


@router.get("/getPixelAt")
def get_pixel_at(
    sensorName: str, x: float, y: float, fromTs: int = None, toTs: int = None
):
    start_time = time.time()
    if fromTs is None and toTs is not None:
        result = [i for i in time_indexes_ts(sensorName) if (i <= toTs)]
    elif fromTs is not None and toTs is None:
        result = [i for i in time_indexes_ts(sensorName) if (i >= fromTs)]
    elif fromTs is not None and toTs is not None:
        result = [i for i in time_indexes_ts(sensorName) if (i >= fromTs and i <= toTs)]
    else:
        result = [i for i in time_indexes_ts(sensorName)]
    result = list(set(result))
    print(result)
    tindexes = ts_to_tindex(result)
    tiles = get_tile_intersection(
        12, [x, y, x, y]
    )  # [n.object for n in index_dat[12].intersection([x,y,x,y], objects=True)]
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    result = []
    for tindex in tindexes:
        ds = load_data(tiles[0], tindex, sensorName)
        geotransform = ds.GetGeoTransform()
        x_offset = int((x - geotransform[0]) / geotransform[1])
        y_offset = int((y - geotransform[3]) / geotransform[5])
        data = [
            ds.GetRasterBand(i).ReadAsArray(x_offset, y_offset, 1, 1)[0][0]
            for i in range(1, ds.RasterCount + 1)
        ]
        data = np.array(data)
        data[np.isnan(data)] = 0
        result.append(data.tolist())
    print("--- %s seconds ---" % (time.time() - start_time))
    return {"error": False, "message": "Success", "data": result}


@router.get("/getDataForAoi/")
def get_data_for_aoi(sensorName: str, level: int, tIndex: int, aoiCode: str):
    start_time = time.time()

    aoi_value = Db.get_aoi_geom_by_aoi_code(aoiCode)
    gj = aoi_value["geom"]
    aoi_geom = ogr.CreateGeometryFromJson(gj)
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    aoi_geom.AssignSpatialReference(target_srs)

    tindex = tIndex
    level = 12

    bbox = aoi_geom.GetEnvelope()
    print(bbox)

    tiles = get_tile_intersection(level, [bbox[0], bbox[2], bbox[1], bbox[3]])
    if tiles is None:
        print("Failed to read sIndex")
        return None
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    for tile in tiles:
        ds = load_data(tile, tIndex, sensorName)
        if ds is not None:
            merge_ds.append(ds)

    out_path = merge_tiles(merge_ds, [bbox[0], bbox[3], bbox[1], bbox[2]])

    print("--- %s seconds ---" % (time.time() - start_time))
    return {"error": False, "message": "Success", "data": out_path}


@router.get("/getDataRefForAoi/")
def get_data_ref_for_aoi(sensorName: str, level: int, tIndex: int, aoiCode: str):
    start_time = time.time()

    aoi_value = Db.get_aoi_geom_by_aoi_code(aoiCode)
    gj = aoi_value["geom"]
    aoi_geom = ogr.CreateGeometryFromJson(gj)
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    aoi_geom.AssignSpatialReference(target_srs)

    tindex = tIndex
    level = 8

    bbox = aoi_geom.GetEnvelope()

    tiles = get_tile_intersection(level, [bbox[0], bbox[2], bbox[1], bbox[3]])
    if tiles is None:
        print("Failed to read sIndex")
        return None
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    for tile in tiles:
        ds = load_data_ref(tile, tIndex, sensorName)
        if ds is not None:
            merge_ds.append(ds)

    print("--- %s seconds ---" % (time.time() - start_time))
    return {"error": False, "message": "Success", "data": merge_ds}


@router.get("/getDataRefsForAoi/")
def get_data_refs_for_aoi(sensorName: str, level: int, tIndexes: str, aoiCode: str):
    start_time = time.time()

    tIndexes = [int(v) for v in tIndexes.split(",")]
    aoi_value = Db.get_aoi_geom_by_aoi_code(aoiCode)
    gj = aoi_value["geom"]
    aoi_geom = ogr.CreateGeometryFromJson(gj)
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    aoi_geom.AssignSpatialReference(target_srs)

    level = 12

    bbox = aoi_geom.GetEnvelope()

    tiles = get_tile_intersection(level, [bbox[0], bbox[2], bbox[1], bbox[3]])
    if tiles is None:
        print("Failed to read sIndex")
        return None
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    for tile in tiles:
        for tIndex in tIndexes:
            ds = load_data_ref(tile, tIndex, sensorName)
            if ds is not None:
                merge_ds.append(ds)

    print("--- %s seconds ---" % (time.time() - start_time))
    return {"error": False, "message": "Success", "data": merge_ds}
