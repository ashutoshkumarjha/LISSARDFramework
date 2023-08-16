
import io
import time
from PIL import Image
import json
import os
from osgeo import ogr, gdal, osr
import random
import string
import scipy.ndimage
import numpy as np
import glob
from retrieval import load_data, merge_tiles_tmp, clip_tile_tmp, load_data_m, load_data_mo
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
    ds = gdal.Warp('', ds, format='VRT', cutlineDSName=fpath, cropToCutline=False, dstNodata=-999, outputType=gdal.GDT_Float32)
    # print(ds.GetRasterBand(1).ReadAsArray()[0,0])
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

def get_mask(val,type='cloud'):
    
    """Get mask for a specific cover type"""

    # convert to binary
    bin_ = '{0:016b}'.format(val)

    # reverse string
    str_bin = str(bin_)[::-1]

    # get bit for cover type
    bits = {'cloud':3,'shadow':4,'dilated_cloud':1,'cirrus':2}
    bit = str_bin[bits[type]]

    if bit == '1':
        return 0 # cover
    else:
        return 1 # no cover

# def get_c_mask(val):
#     if '{0:016b}'.format(val)[::-1][14:16][::-1] == '11':
#         return 0
#     # elif '{0:016b}'.format(val)[-5] == '1':
#     #     return 0
#     else:
#         return 1
#     return 1

def render_png_multits(tiles, tIndexes, sensorName, bbox, aoi_geom, bands, dataset_def, vmax, vmin):
    # print(vmax)
    start_time = time.time()
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    sat_refs = []
    for tile in tiles:
        _merge_ds = load_data_m(tile, tIndexes, sensorName, bbox)
        merge_ds = merge_ds + _merge_ds
        # for tIndex in tIndexes:
        #     ds = load_data(tile, tIndex, sensorName, sat_refs, bbox)
        #     if ds == 'NO':
        #         break
        #     if ds is not None:
        #         merge_ds.append(ds)
    print("MERGE_DS: %ss" % (round(time.time() - start_time, 3)))

    # print(len(merge_ds))
    # print(sat_refs)
    # merge_ds = [merge_ds[0]]

    if len(merge_ds) > 0:
        if len(merge_ds) == 1:
            out_ds = merge_ds[0]
            out_ds = clip_tile_tmp(out_ds, bbox)
            # print(out_ds.GetRasterBand(1).ReadAsArray())
        if len(merge_ds) > 1:
            out_ds = merge_tiles_tmp(merge_ds, bbox)
        print("MERGE_DATA: %ss" % (round(time.time() - start_time, 3)))
        # print(out_ds.GetRasterBand(1).ReadAsArray())
        
        out_ds = clip_raster_ds_by_geom(out_ds, aoi_geom)
        # print(out_ds.GetRasterBand(1).ReadAsArray())
        print("CLIP_DATA: %ss" % (round(time.time() - start_time, 3)))

        if bands is None:
            rgb_bands = [2, 3, 4]
        else:
            rgb_bands = [int(b) for b in bands.split(",")]

        if dataset_def["no_of_bands"] == 1:
            rgb_bands = [1, 1, 1]
        
        if len(bands) == 1:
            band_no = int(bands[0])
            rgb_bands = [band_no, band_no, band_no]

        rgb_data = []
        alpha_data = []
#        vmax = 0.2
        vmin = 0
        num_nonzs = []

        # cloud_band_data = out_ds.GetRasterBand(out_ds.RasterCount).ReadAsArray()
        # cloud_mask = np.vectorize(get_mask)(cloud_band_data,type='cloud')
        # shadow_mask = np.vectorize(get_mask)(cloud_band_data,type='shadow')
        # dilated_cloud_mask = np.vectorize(get_mask)(cloud_band_data,type='dilated_cloud')
        # cirrus_mask = np.vectorize(get_mask)(cloud_band_data,type='cirrus')
        # cloud_masks = cloud_mask # np.vectorize(get_c_mask)(cloud_band_data) #
        # cloud_masks[cloud_masks>0] = 1
        # cloud_masks = cloud_band_data

        for bid in rgb_bands:
            data = out_ds.GetRasterBand(bid).ReadAsArray().astype(np.float64)
            # data = cloud_masks.astype(np.float64)
            # data[data>=55052] = -999
            # data = np.where(cloud_masks, data, -999)
            data[data<=-999] = np.nan
            data = (
                data * dataset_def["scale_factor"]
                + dataset_def["value_offset"]
            )
            # print(data[0,0])
            # print(out_ds.GetRasterBand(bid).ReadAsArray()[0,0])
            # data[data<=-999] = np.nan
            data[data<=vmin] = vmin
            data[data>vmax] = vmax
            # print(np.nanmin(data), np.nanmax(data))
            # data[data <= dataset_def["value_offset"]] = np.nan
            # num_nonz = data.size - np.count_nonzero(np.isnan(data))
            # if num_nonz in num_nonzs:
            #     print("Data not needed")
            # num_nonzs.append(num_nonz)
            # data[data == 0] = -5
            # data = data + 0.9
            # data[data < 0] = 0
            zoom_factors = (256 / out_ds.RasterYSize, 256 / out_ds.RasterXSize)
            data = scipy.ndimage.zoom(data, zoom=zoom_factors, order=0, mode='nearest')
            data = (data.astype(np.float64) -vmin) / (vmax-vmin)  # np.nanmax(data)
            data = 255 * data
            data[data < 0] = 0
            data[data == 0] = 1
            data = np.nan_to_num(data)
            data = data.astype(np.uint8)
            # print(np.nanmin(data), np.nanmax(data))
            rgb_data.append(data)
#        print(rgb_data)

        print("READ_DATA: %ss" % (round(time.time() - start_time, 3)))
        
        alpha_data = np.sum(np.array(rgb_data), axis=0)
        alpha_data[alpha_data > 0] = 255
        rgb_data.append(alpha_data)

        rgb_data = np.array(rgb_data, dtype=np.uint8)
        # rgb_data[:, 25,0] = [255, 0, 0, 255]
        # print(rgb_data[:, 25,0])

        rgb_data = np.array(rgb_data)

        rgb_data = np.ascontiguousarray(rgb_data.transpose(1, 2, 0))
        img = Image.fromarray(rgb_data, "RGBA")
        return img
    else:
        print("No ds")
        return None
#render_png_multits

def render_png_multits_pre(merge_ds, bbox, aoi_geom, bands, dataset_def, vmax, vmin):
    # print(vmax)
    start_time = time.time()
    # out_ds = gdal.Open(merge_ds[0])
    # b = out_ds.GetRasterBand(1).ReadAsArray()
    # print(b)
    if len(merge_ds) > 0:
        if len(merge_ds) == 1:
            out_ds = merge_ds[0]
            out_ds = clip_tile_tmp(out_ds, bbox)
            # print(out_ds.GetRasterBand(1).ReadAsArray())
        if len(merge_ds) > 1:
            out_ds = merge_tiles_tmp(merge_ds, bbox)
        print("MERGE_DATA: %ss" % (round(time.time() - start_time, 3)))
        # print(out_ds.GetRasterBand(1).ReadAsArray())
        
        out_ds = clip_raster_ds_by_geom(out_ds, aoi_geom)
        # print(out_ds.GetRasterBand(1).ReadAsArray())
        print("CLIP_DATA: %ss" % (round(time.time() - start_time, 3)))

        if bands is None:
            rgb_bands = [2, 3, 4]
        else:
            rgb_bands = [int(b) for b in bands.split(",")]

        if dataset_def["no_of_bands"] == 1:
            rgb_bands = [1, 1, 1]
        
        if len(bands) == 1:
            band_no = int(bands[0])
            rgb_bands = [band_no, band_no, band_no]

        rgb_data = []
        alpha_data = []
#        vmax = 0.2
        # vmin = 0
        num_nonzs = []

        # cloud_band_data = out_ds.GetRasterBand(out_ds.RasterCount).ReadAsArray()
        # cloud_mask = np.vectorize(get_mask)(cloud_band_data,type='cloud')
        # shadow_mask = np.vectorize(get_mask)(cloud_band_data,type='shadow')
        # dilated_cloud_mask = np.vectorize(get_mask)(cloud_band_data,type='dilated_cloud')
        # cirrus_mask = np.vectorize(get_mask)(cloud_band_data,type='cirrus')
        # cloud_masks = cloud_mask # np.vectorize(get_c_mask)(cloud_band_data) #
        # cloud_masks[cloud_masks>0] = 1
        # cloud_masks = cloud_band_data

        for bid in rgb_bands:
            data = out_ds.GetRasterBand(bid).ReadAsArray().astype(np.float32)
            # print(data)
            # data = cloud_masks.astype(np.float64)
            # data[data>=55052] = -999
            # data = np.where(cloud_masks, data, -999)
            data[data<=-999] = np.nan
            # data = (
            #     data * dataset_def["scale_factor"]
            #     + dataset_def["value_offset"]
            # )
            # print(data)
            # print(out_ds.GetRasterBand(bid).ReadAsArray()[0,0])
            # data[data<=-999] = np.nan
            data[data<=vmin] = vmin
            data[data>vmax] = vmax
            # print(np.nanmin(data), np.nanmax(data))
            # data[data <= dataset_def["value_offset"]] = np.nan
            # num_nonz = data.size - np.count_nonzero(np.isnan(data))
            # if num_nonz in num_nonzs:
            #     print("Data not needed")
            # num_nonzs.append(num_nonz)
            # data[data == 0] = -5
            # data = data + 0.9
            # data[data < 0] = 0
            zoom_factors = (256 / out_ds.RasterYSize, 256 / out_ds.RasterXSize)
            data = scipy.ndimage.zoom(data, zoom=zoom_factors, order=0, mode='nearest')
            data = (data.astype(np.float64) -vmin) / (vmax-vmin)  # np.nanmax(data)
            data = 255 * data
            data[data < 0] = 0
            data[data == 0] = 1
            data = np.nan_to_num(data)
            data = data.astype(np.uint8)
            # print(np.nanmin(data), np.nanmax(data))
            rgb_data.append(data)
            # print(data)
#        print(rgb_data)

        print("READ_DATA: %ss" % (round(time.time() - start_time, 3)))
        
        alpha_data = np.sum(np.array(rgb_data), axis=0)
        alpha_data[alpha_data > 0] = 255
        rgb_data.append(alpha_data)

        rgb_data = np.array(rgb_data, dtype=np.uint8)
        # rgb_data[:, 25,0] = [255, 0, 0, 255]
        # print(rgb_data[:, 25,0])

        rgb_data = np.array(rgb_data)

        rgb_data = np.ascontiguousarray(rgb_data.transpose(1, 2, 0))
        img = Image.fromarray(rgb_data, "RGBA")
        return img
    else:
        print("No ds")
        return None



def render_png_multits_o(tiles, tIndexes, outputName, bbox, bands, vmax, vmin):
    # print(vmax)
    start_time = time.time()
    tiles = [[int(i) for i in tile.split("#")] for tile in tiles]
    merge_ds = []
    sat_refs = []
    for tile in tiles:
        _merge_ds = load_data_mo(tile, tIndexes, outputName, bbox)
        merge_ds = merge_ds + _merge_ds
    print("MERGE_DS: %ss" % (round(time.time() - start_time, 3)))

    if len(merge_ds) > 0:
        if len(merge_ds) == 1:
            out_ds = merge_ds[0]
            out_ds = clip_tile_tmp(out_ds, bbox)
        if len(merge_ds) > 1:
            out_ds = merge_tiles_tmp(merge_ds, bbox)
        print("MERGE_DATA: %ss" % (round(time.time() - start_time, 3)))
        # print(out_ds.GetRasterBand(1).ReadAsArray())
        
        # out_ds = clip_raster_ds_by_geom(out_ds, aoi_geom)
        # print(out_ds.GetRasterBand(1).ReadAsArray())
        print("CLIP_DATA: %ss" % (round(time.time() - start_time, 3)))

        if bands is None:
            rgb_bands = [2, 3, 4]
        else:
            rgb_bands = [int(b) for b in bands.split(",")]

        if out_ds.RasterCount == 1:
            rgb_bands = [1, 1, 1]
        
        if len(bands) == 1:
            band_no = int(bands[0])
            rgb_bands = [band_no, band_no, band_no]

        rgb_data = []
        alpha_data = []
#        vmax = 0.2
        # vmin = 0
        num_nonzs = []

        # cloud_band_data = out_ds.GetRasterBand(out_ds.RasterCount).ReadAsArray()
        # cloud_mask = np.vectorize(get_mask)(cloud_band_data,type='cloud')
        # shadow_mask = np.vectorize(get_mask)(cloud_band_data,type='shadow')
        # dilated_cloud_mask = np.vectorize(get_mask)(cloud_band_data,type='dilated_cloud')
        # cirrus_mask = np.vectorize(get_mask)(cloud_band_data,type='cirrus')
        # cloud_masks = cloud_mask # np.vectorize(get_c_mask)(cloud_band_data) #
        # cloud_masks[cloud_masks>0] = 1
        # cloud_masks = cloud_band_data

        for bid in rgb_bands:
            data = out_ds.GetRasterBand(bid).ReadAsArray().astype(np.float64)
            data[data==out_ds.GetRasterBand(bid).GetNoDataValue()] = np.nan
            # print(data)
            # data = cloud_masks.astype(np.float64)
            # data[data>=55052] = -999
            # data = np.where(cloud_masks, data, -999)
            data[data<=-999] = np.nan
            # data = (
            #     data * dataset_def["scale_factor"]
            #     + dataset_def["value_offset"]
            # )
            # print(data[0,0])
            # print(out_ds.GetRasterBand(bid).ReadAsArray()[0,0])
            # data[data<=-999] = np.nan
            # vmin = -0.1 #np.nanmin(data)
            # vmax = 0.11 #np.nanmax(data)
            data[data<=vmin] = vmin
            data[data>vmax] = vmax
            # print(np.nanmin(data), np.nanmax(data))
            # data[data <= dataset_def["value_offset"]] = np.nan
            # num_nonz = data.size - np.count_nonzero(np.isnan(data))
            # if num_nonz in num_nonzs:
            #     print("Data not needed")
            # num_nonzs.append(num_nonz)
            # data[data == 0] = -5
            # data = data + 0.9
            # data[data < 0] = 0
            zoom_factors = (256 / out_ds.RasterYSize, 256 / out_ds.RasterXSize)
            data = scipy.ndimage.zoom(data, zoom=zoom_factors, order=0, mode='nearest')
            data = (data.astype(np.float64) -vmin) / (vmax-vmin)  # np.nanmax(data)
            data = 255 * data
            data[data < 0] = 0
            data[data == 0] = 1
            data = np.nan_to_num(data)
            data = data.astype(np.uint8)
            # print(np.nanmin(data), np.nanmax(data))
            rgb_data.append(data)
#        print(rgb_data)

        # print(np.isnan(rgb_data[0]).all())
        print("READ_DATA: %ss" % (round(time.time() - start_time, 3)))
        
        alpha_data = np.sum(np.array(rgb_data), axis=0)
        alpha_data[alpha_data > 0] = 255
        rgb_data.append(alpha_data)

        rgb_data = np.array(rgb_data, dtype=np.uint8)
        # rgb_data[:, 25,0] = [255, 0, 0, 255]
        # print(rgb_data[:, 25,0])

        rgb_data = np.array(rgb_data)

        rgb_data = np.ascontiguousarray(rgb_data.transpose(1, 2, 0))
        img = Image.fromarray(rgb_data, "RGBA")
        return img
    else:
        print("No ds")
        return None
#render_png_multits
