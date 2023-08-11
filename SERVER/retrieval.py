from osgeo import gdal, ogr, osr
import os
import osgeo
import json
from datetime import datetime
import math
import glob
import zCurve as z
from db import Db
from utils import generate_string, tilenum2deg
import config as app_config


config = app_config.config

def load_data(tile, tindex, sensor_name):
    ds_def = Db.get_db_dataset_def_by_name(sensor_name)
    ds_id = ds_def['dataset_id']
    dir_path = config["tile_dir"]
    zoom_level = tile[0]
    x_index = tile[1]
    y_index = tile[2]
    z_index = z.interlace(tindex, y_index, x_index)
    tile_data = Db.get_db_tile_by_zindex_zoom_ds(z_index, zoom_level, ds_id, x_index, y_index, tindex)
    if tile_data is None:
        return None
    file_path = os.path.join(dir_path, tile_data['file_path'])
    if(not os.path.exists(file_path)):
        print("No data", file_path)
        return None
    ds = gdal.Open(file_path)
    return ds

def load_data_ref(tile, tindex, sensor_name):
    ds_def = Db.get_db_dataset_def_by_name(sensor_name)
    ds_id = ds_def['dataset_id']
    dir_path = config["tile_dir"]
    zoom_level = tile[0]
    x_index = tile[1]
    y_index = tile[2]
    z_index = z.interlace(tindex, y_index, x_index)
    tile_data = Db.get_db_tile_by_zindex_zoom_ds(z_index, zoom_level, ds_id, x_index, y_index, tindex)
    if tile_data is None:
        return None
    file_path = os.path.join(dir_path, tile_data['file_path'])
    if(not os.path.exists(file_path)):
        return None
    return file_path

def merge_tiles(merge_ds, projWin):
    vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic')
    merge_vrt = gdal.BuildVRT('', merge_ds, options=vrt_options)
    merge_ds = gdal.Warp("", merge_vrt, format="VRT")
    out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    merge_ds = gdal.Translate(out_path, merge_ds, format='GTiff', projWin = projWin, projWinSRS='EPSG:4326')
    return out_path

def merge_tiles_tmp(merge_ds, projWin):
    vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic')
    merge_vrt = gdal.BuildVRT('', merge_ds, options=vrt_options)
    merge_ds = gdal.Warp("", merge_vrt, format="VRT")
    merge_ds = gdal.Translate("", merge_ds, format='VRT', projWin = projWin, projWinSRS='EPSG:4326')
    return merge_ds

def clean_tmp_dir():
    files = glob.glob(config["temp_dir"]+"/*tif")
    for f in files:
        os.remove(f)
    return True

def time_indexes(sensor_name):
    start_ts = int(datetime.timestamp(datetime.strptime(config["start_time"], '%Y-%m-%d %H:%M:%S'))*1000)
    results = json.load(open(os.path.join(config["tindex_dir"], f"{sensor_name}.json")))
    results = results["data"]
    return [r for r in results]

def time_indexes_ts(sensor_name):
    start_ts = int(datetime.timestamp(datetime.strptime(config["start_time"], '%Y-%m-%d %H:%M:%S'))*1000)
    results = json.load(open(os.path.join(config["tindex_dir"], f"{sensor_name}.json")))
    results = results["data"]
    results = list(set([start_ts + r*1000 for r in results]))
    results.sort()
    return results

def ts_to_tindex(ts):
    start_ts = int(datetime.timestamp(datetime.strptime(config["start_time"], '%Y-%m-%d %H:%M:%S'))*1000)
    return [int((t-start_ts)/1000) for t in ts]


def tindex_to_ts(ts):
    start_ts = int(datetime.timestamp(datetime.strptime(config["start_time"], '%Y-%m-%d %H:%M:%S'))*1000)
    return [start_ts + r*1000 for r in ts]

def get_xyz_tile_res(bbox):
    return (bbox[2]-bbox[0])/256
