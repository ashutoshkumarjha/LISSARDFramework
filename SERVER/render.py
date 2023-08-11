
import io
from PIL import Image
import json
import os
from osgeo import ogr, gdal, osr
import random
import string
import scipy.ndimage
import numpy as np
import glob
from retrieval import load_data, merge_tiles_tmp
import config as app_config

def image_to_byte_array(image: Image):
  # BytesIO is a fake file stored in memory
  imgByteArr = io.BytesIO()
  # image.save expects a file as a argument, passing a bytes io ins
  image.save(imgByteArr, format='PNG')
  
  # Turn the BytesIO object back into a bytes object
  imgByteArr = imgByteArr#.getvalue()
  imgByteArr.seek(0)
  return imgByteArr

def clip_raster_ds_by_geom(ds, geom):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    config = app_config.config
    fname = ''.join(random.choices(string.ascii_uppercase, k=16))
    fpath = os.path.join(config['temp_dir'], f'{fname}.shp')
    memory_ds = driver.CreateDataSource(fpath)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    memory_layer = memory_ds.CreateLayer('Layer', srs, geom_type=ogr.wkbPolygon)
    feature = ogr.Feature(memory_layer.GetLayerDefn())
    feature.SetGeometry(geom)
    memory_layer.CreateFeature(feature)
    memory_layer = None
    memory_ds = None
    ds = gdal.Warp('', ds, format='VRT', cutlineDSName=fpath, cropToCutline=False)
    try:
        for temp_file in glob.glob(os.path.join(config['temp_dir'], f'{fname}*')):
            if(os.path.exists(temp_file)):
                os.remove(temp_file)
    except Exception as e:
        print(e)
    return ds


def render_png(tiles, tIndex, sensorName, bbox, aoi_geom, bands, dataset_def, vmax):
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    for tile in tiles: 
        ds = load_data(tile, tIndex, sensorName)
        if(ds is not None):
            merge_ds.append(ds)
        
    if len(merge_ds) > 0:
        out_ds = merge_tiles_tmp(merge_ds, bbox)
        out_ds = clip_raster_ds_by_geom(out_ds, aoi_geom)

        if(bands is None):
            rgb_bands = [2,3,4]
        else:
            rgb_bands = [int(b) for b in bands.split(',')]
        
        if(dataset_def['no_of_bands']==1):
            rgb_bands = [1,1,1]
        
        rgb_data = []
        alpha_data = []
        # vmax = 1


        for bid in rgb_bands:
            data = out_ds.GetRasterBand(bid).ReadAsArray() * dataset_def['scale_factor'] + dataset_def['value_offset']
            zoom_factors = (256/out_ds.RasterYSize, 256/out_ds.RasterXSize)
            data = scipy.ndimage.zoom(data, zoom=zoom_factors, order=0)
            data = np.nan_to_num(data)
            data = data.astype(np.float64) / vmax #np.nanmax(data)
            data = 255 * data
            data[data<0] = 0
            data = data.astype(np.uint8)
            rgb_data.append(data)
        
        alpha_data = np.sum(np.array(rgb_data), axis=0)
        alpha_data[alpha_data>0] = 255
        rgb_data.append(alpha_data)

        rgb_data = np.array(rgb_data, dtype=np.uint8)

        rgb_data = np.array(rgb_data)
        
        rgb_data = np.ascontiguousarray(rgb_data.transpose(1,2,0))
        img = Image.fromarray(rgb_data, 'RGBA')
        return img
    else:
        print("No ds")
        return None