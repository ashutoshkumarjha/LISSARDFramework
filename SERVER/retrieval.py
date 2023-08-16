from osgeo import gdal, ogr, osr
import os
import osgeo
import json
from datetime import datetime
import math
import glob
import numpy as np
import zCurve as z
from db import Db
from utils import generate_string, tilenum2deg
import config as app_config


config = app_config.config
driver = gdal.GetDriverByName('GTiff')

def load_data_m(tile, tindexes, sensor_name, projWin):
    ds_def = Db.get_db_dataset_def_by_name(sensor_name)
    ds_id = ds_def['dataset_id']
    dir_path = config["tile_dir"]
    zoom_level = tile[0]
    x_index = tile[1]
    y_index = tile[2]
    z_indexes = [str(z.interlace(tindex, y_index, x_index)) for tindex in tindexes]
    tindexes = [str(ti) for ti in tindexes]
    tile_datas = Db.get_db_tile_by_zindex_zoom_ds_distinct(z_indexes, zoom_level, ds_id, x_index, y_index, tindexes)

    merge_ds = []

    for tile_data in tile_datas:
        # print(tile_data)
        file_path = os.path.join(dir_path, tile_data['file_path'])
        if(not os.path.exists(file_path)):
            print("No data", file_path)
            continue
        ds = gdal.Open(file_path)
        gt = ds.GetGeoTransform()
        i1 = int((projWin[0] - gt[0])/gt[1])
        i2 = int((projWin[2] - gt[0])/gt[1])
        j1 = int((projWin[1] - gt[3])/gt[5])
        j2 = int((projWin[3] - gt[3])/gt[5])
        if i1 < 0 or i2 < 0 or j1 < 0 or j2 < 0:
            continue
        if i1 > 256 or i2 > 256 or j1 > 256 or j2 > 256:
            continue
        merge_ds.append(ds)
        print(file_path)
    return merge_ds

def load_data_mo(tile, tindexes, output_name, projWin):
    dir_path = config["tile_dir"]
    zoom_level = tile[0]
    x_index = tile[1]
    y_index = tile[2]
    z_indexes = [str(z.interlace(tindex, y_index, x_index)) for tindex in tindexes]
    tindexes = [str(ti) for ti in tindexes]
    tile_datas = Db.get_db_tile_by_zindex_zoom_outds_distinct(z_indexes, zoom_level, x_index, y_index, tindexes)

    merge_ds = []

    for tile_data in tile_datas:
        # print(tile_data)
        file_path = os.path.join(dir_path, tile_data['file_path'])
        if(not os.path.exists(file_path)):
            print("No data", file_path)
            continue
        print(file_path)
        ds = gdal.Open(file_path)
        gt = ds.GetGeoTransform()
        i1 = int((projWin[0] - gt[0])/gt[1])
        i2 = int((projWin[2] - gt[0])/gt[1])
        j1 = int((projWin[1] - gt[3])/gt[5])
        j2 = int((projWin[3] - gt[3])/gt[5])
        if i1 < 0 or i2 < 0 or j1 < 0 or j2 < 0:
            continue
        if i1 > 256 or i2 > 256 or j1 > 256 or j2 > 256:
            continue
        merge_ds.append(ds)
        print(file_path)
    return merge_ds

def load_data(tile, tindex, sensor_name, sat_refs, projWin):
    ds_def = Db.get_db_dataset_def_by_name(sensor_name)
    ds_id = ds_def['dataset_id']
    dir_path = config["tile_dir"]
    zoom_level = tile[0]
    x_index = tile[1]
    y_index = tile[2]
    z_index = z.interlace(tindex, y_index, x_index)
    tile_data = Db.get_db_tile_by_zindex_zoom_ds_sat_ref(z_index, zoom_level, ds_id, x_index, y_index, tindex, sat_refs)
    if tile_data is None:
        return 'NO'
    # if tile_data['sat_ref'] in sat_refs:
    #     return None
    if tile_data is None:
        return None
    file_path = os.path.join(dir_path, tile_data['file_path'])
    if(not os.path.exists(file_path)):
        print("No data", file_path)
        return None
    ds = gdal.Open(file_path)

    gt = ds.GetGeoTransform()
    # print(projWin)
    # print(gt)
    i1 = int((projWin[0] - gt[0])/gt[1])
    i2 = int((projWin[2] - gt[0])/gt[1])
    j1 = int((projWin[1] - gt[3])/gt[5])
    j2 = int((projWin[3] - gt[3])/gt[5])
    # print(i1, i2, j1, j2)
    if i1 < 0 or i2 < 0 or j1 < 0 or j2 < 0:
        return "NO"
    if i1 > 256 or i2 > 256 or j1 > 256 or j2 > 256:
        return "NO"
    sat_refs.append(tile_data['sat_ref'])
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
    # file_path = os.path.join(dir_path, tile_data['file_path'])
    file_path = tile_data['file_path']
    # if(not os.path.exists(file_path)):
    #     return None
    return file_path

def load_data_refs(tiles, tindexes, ds_id, zoom_level):
    dir_path = config["tile_dir"]
    z_indexes = []
    for tindex in tindexes:
        z_indexe = [str(z.interlace(tindex, tile[2], tile[1])) for tile in tiles]
        for z_index in z_indexe:
            z_indexes.append(z_index)
    tile_datas = Db.get_db_tile_by_zindex_zoom_dses(z_indexes, zoom_level, ds_id)
    if tile_datas is None:
        return None
    file_paths = [os.path.join(dir_path, tile_data['file_path']) for tile_data in tile_datas]
    # file_path = tile_data['file_path']
    # if(not os.path.exists(file_path)):
    #     return None
    return file_paths

def merge_tiles(merge_ds, projWin):
    vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic')
    merge_vrt = gdal.BuildVRT('', merge_ds, options=vrt_options)
    merge_ds = gdal.Warp("", merge_vrt, format="VRT")
    out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    merge_ds = gdal.Translate(out_path, merge_ds, format='GTiff', projWin = projWin, projWinSRS='EPSG:4326')
    return out_path

def merge_tiles_tmp(merge_ds, projWin):
    vrt_options = gdal.BuildVRTOptions(resampleAlg='near')
    merge_vrt = gdal.BuildVRT('', merge_ds, options=vrt_options)
    merge_ds = gdal.Warp("", merge_vrt, format="VRT")
    merge_ds = gdal.Translate("", merge_ds, format='VRT', projWin = projWin, projWinSRS='EPSG:4326')
    return merge_ds

def clip_tile_tmp(merge_ds, projWin):
    # vrt_options = gdal.BuildVRTOptions(resampleAlg='cubic')
    # merge_vrt = gdal.BuildVRT('', merge_ds, options=vrt_options)
    # merge_ds = gdal.Warp("", merge_vrt, format="VRT")
    # merge_ds = gdal.Warp("", merge_ds, format="MEM")
    # print(merge_ds.GetRasterBand(1).ReadAsArray())
    # print(projWin, merge_ds.GetGeoTransform())
    # gt = merge_ds.GetGeoTransform()
    # print(projWin)
    # print(gt)
    # i1 = int((projWin[0] - gt[0])/gt[1])
    # i2 = int((projWin[2] - gt[0])/gt[1])
    # j1 = int((projWin[1] - gt[3])/gt[5])
    # j2 = int((projWin[3] - gt[3])/gt[5])
    # print(i1, i2, j1, j2)
    # out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    merge_ds = gdal.Translate("", merge_ds, format='MEM', projWin = projWin, projWinSRS='EPSG:4326')
    # print(merge_ds.GetRasterBand(1).ReadAsArray())
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

def do_ndi(ds, b1, b2):
    out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    out_data = None
    ds = gdal.Open(ds)
    b1 = ds.GetRasterBand(b1+1).ReadAsArray().astype(np.float32)
    b2 = ds.GetRasterBand(b2+1).ReadAsArray().astype(np.float32)
    out_data = (b1-b2)/(b1+b2)
    out_ds = driver.Create(out_path, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32)
    b = out_ds.GetRasterBand(1)
    b.WriteArray(out_data)
    b.FlushCache()
    out_ds.SetProjection(ds.GetProjection())
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    return out_path


def do_avg(ds1, ds2):
    out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    ds1 = gdal.Open(ds1)
    ds2 = gdal.Open(ds2)
    out_ds = driver.Create(out_path, ds1.RasterXSize, ds1.RasterYSize, ds1.RasterCount, gdal.GDT_Float32)
    for bno in range(ds1.RasterCount):
        b1 = ds1.GetRasterBand(bno+1).ReadAsArray().astype(np.float32)
        b2 = ds2.GetRasterBand(bno+1).ReadAsArray().astype(np.float32)
        out_data = (b1 + b2)/2
        b = out_ds.GetRasterBand(bno+1)
        b.WriteArray(out_data)
        b.FlushCache()
    out_ds.SetProjection(ds1.GetProjection())
    out_ds.SetGeoTransform(ds1.GetGeoTransform())
    return out_path

def do_dif(ds1, ds2):
    out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    ds1 = gdal.Open(ds1)
    ds2 = gdal.Open(ds2)
    out_ds = driver.Create(out_path, ds1.RasterXSize, ds1.RasterYSize, ds1.RasterCount, gdal.GDT_Float32)
    for bno in range(ds1.RasterCount):
        b1 = ds1.GetRasterBand(bno+1).ReadAsArray().astype(np.float32)
        b2 = ds2.GetRasterBand(bno+1).ReadAsArray().astype(np.float32)
        out_data = (b1 - b2)
        b = out_ds.GetRasterBand(bno+1)
        b.WriteArray(out_data)
        b.FlushCache()
    out_ds.SetProjection(ds1.GetProjection())
    out_ds.SetGeoTransform(ds1.GetGeoTransform())
    return out_path

def scale_data(ds, dataset_def):
    out_path = os.path.join(config["temp_dir"], f'{generate_string()}.tif')
    ds = gdal.Open(ds)
    out_ds = driver.Create(out_path, ds.RasterXSize, ds.RasterYSize, ds.RasterCount, gdal.GDT_Float32)
    for bno in range(ds.RasterCount):
        b1 = ds.GetRasterBand(bno+1).ReadAsArray().astype(np.float32)
        out_data = (
            b1 * dataset_def["scale_factor"]
            + dataset_def["value_offset"]
        )
        b = out_ds.GetRasterBand(bno+1)
        b.WriteArray(out_data)
        b.FlushCache()
    out_ds.SetProjection(ds.GetProjection())
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    return out_path