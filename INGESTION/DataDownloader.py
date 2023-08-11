from dotenv import load_dotenv
from pystac_client import Client
import json
import os
import boto3
import rasterio as rio
from rasterio.mask import mask
from rasterio.session import AWSSession
from matplotlib.pyplot import imshow
from rasterio.features import bounds
from pyproj import Transformer
import matplotlib.pyplot as plt
from osgeo import gdal, osr, ogr
import osgeo
import asyncio
from datetime import datetime
from DataIngestion import partition_data

load_dotenv(dotenv_path='../app.env')

AWS_ACCESS_KEY = os.getenv('GCP_PROJECT_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('SERVICE_ACCOUNT_FILE')
DOWNLOAD_DIR = "/projects/data/project/raw1"

class DataDownloader:

    def get_subset(geotiff_file, bbox):
        aws_session = AWSSession(boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY), requester_pays=True)
        with rio.Env(aws_session):
            with rio.open(geotiff_file) as geo_fp:
                Transf = Transformer.from_crs("epsg:4326", geo_fp.crs) 
                lon_west, lat_north = Transf.transform(bbox[3], bbox[0])
                lon_east, lat_south = Transf.transform(bbox[1], bbox[2]) 
                x_top, y_top = geo_fp.index( lon_west, lat_north )
                x_bottom, y_bottom = geo_fp.index( lon_east, lat_south )
                window = rio.windows.Window.from_slices( ( x_top, x_bottom ), ( y_top, y_bottom ) )            
                subset = geo_fp.read(1, window=window)
                y1 = lat_south
                x1 = lon_west
                res = geo_fp.transform[0]
                transform = Affine.translation(x1 - res / 2, y1 - res / 2) * Affine.scale(res, -res)
        return subset, transform, geo_fp.crs
    
    def get_mask(geotiff_file, furl, aoi_geom):
        geometry = ogr.CreateGeometryFromJson(str(aoi_geom))
        aws_session = AWSSession(boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY), requester_pays=True)
        with rio.Env(aws_session):
            with rio.open(furl) as geo_fp:
                geometry = DataDownloader.reproject(geometry, 4326, int(str(geo_fp.crs)[5:]))
                out_image, transformed = mask(geo_fp, [json.loads(geometry.ExportToJson())], crop=True, filled=True)
                out_profile = geo_fp.profile.copy()
                out_profile.update({'width': out_image.shape[2],'height': out_image.shape[1], 'transform': transformed})
                with rio.open(geotiff_file, 'w', **out_profile) as dst:
                    dst.write(out_image)
        return True
    
    def subset_to_file(out_file, data, gt, crs):
        out_ds = rio.open(
            out_file,
            'w',
            driver='GTiff',
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype=data.dtype,
            crs=crs,
            transform=gt,
        )
        out_ds.write(data, 1)
        out_ds.close()
    
    def reproject(geometry, in_srs, out_srs):
        src_srs = osr.SpatialReference()
        src_srs.ImportFromEPSG(in_srs)
        target_srs = osr.SpatialReference()
        if int(osgeo.__version__[0]) >= 3:
            target_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
            src_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
        target_srs.ImportFromEPSG(out_srs)
        transform = osr.CoordinateTransformation(src_srs, target_srs)
        geometry.Transform(transform)
        return geometry
    
    def for_shp(aoi_shp_path, params):
        aoi_ds = ogr.Open(aoi_shp_path)
        for feature in aoi_ds.GetLayer():
            aoi_geom = feature.GetGeometryRef().ExportToJson()
            break
        # print(json.loads(aoi_geom).keys())
        DataDownloader.download_data(aoi_geom, params)

    def for_geojson(aoi_gj_path, params):
        aoi = json.load(open(aoi_gj_path))
        geometry = aoi["features"][0]["geometry"]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(DataDownloader.download_data(geometry, params, loop))
        print("-------DOWNLOADED--------")
        return
        

    def download_scene(scene, aoi_geom, sensor, params, bands, pathkey, rowkey):
        scene_geometry = ogr.CreateGeometryFromJson(str(scene['geometry']))
        aoi_geometry = ogr.CreateGeometryFromJson(str(aoi_geom))
        scene_intersect_area = DataDownloader.reproject(scene_geometry.Intersection(aoi_geometry), 4326, 32646).GetArea()
        
        if True or scene_intersect_area > 100000000: #25sqkm
            row_path = scene['properties'][pathkey] + scene['properties'][rowkey]
            if "rows_paths" in params:
                if not row_path in params["rows_paths"]:
                    return
            
            print(scene['id'])

            scene_dir = os.path.join(DOWNLOAD_DIR, scene['id'])
            merged_file = os.path.join(scene_dir, scene['id'] + ".tif")
            if not os.path.exists(scene_dir):
                os.makedirs(scene_dir)
            
            #write meta
            with open(os.path.join(scene_dir, f"meta.txt"), "w") as fp:
                meta = {
                    "sensor": "Landsat_OLI",
                    "dateTime": int(datetime.strptime(scene['properties']['datetime'][:19], "%Y-%m-%dT%H:%M:%S").timestamp() * 1000),
                    "srcPath": merged_file
                }
                json.dump(meta, fp)

            tmp_band_files = []
            bid = 1
            for band in bands:
                url = None
                if sensor == 'S2':
                    url = scene['assets'][band]['href']
                else:
                    url = scene['assets'][band]['alternate']['s3']['href']
                
                print(f"Downloading: {band}")

                tmp_band_file = os.path.join(scene_dir, f'tmp_B{str(bid).zfill(2)}.tif')
                band_file = os.path.join(scene_dir, f'tmp_B{str(bid).zfill(2)}.tif')

                flg = DataDownloader.get_mask(tmp_band_file, url, aoi_geom)
                
                tmp_band_files.append(tmp_band_file)
                bid += 1
                
            merged_ds = gdal.BuildVRT("", tmp_band_files, separate=True)
            merged_ds = gdal.Translate(merged_file, merged_ds, format="GTiff", xRes=60, yRes=60, resampleAlg='nearest')
            merged_ds = None
            for _tmpfile in tmp_band_files:
                os.remove(_tmpfile)
            partition_data(meta["srcPath"], meta["dateTime"], meta["sensor"])

    async def aync_download_scene(loop, scene, aoi_geom, sensor, params, bands, pathkey, rowkey):
        return await loop.run_in_executor(
            None, DataDownloader.download_scene, scene, aoi_geom, sensor, params, bands, pathkey, rowkey
        )

    async def download_data(aoi_geom, params, loop):
        start_date = None
        end_date = None
        sensor = None
        cloud_cover = 95
        
        if "start_date" in params:
            start_date = params["start_date"]
        
        if "end_date" in params:
            end_date = params["end_date"]
        
        if "sensor" in params:
            sensor = params["sensor"]
        
        if "cloud_cover" in params:
            cloud_cover = params["cloud_cover"]

        if (
            start_date is None or
            end_date is None or
            sensor is None):
            print("Invalid params")
            return None

        platforms = None
        stack_server_url = None
        collection = None
        bands = None
        rowkey = None
        pathkey = None
        
        if sensor == 'L8':
            stack_server_url = 'https://landsatlook.usgs.gov/stac-server'
            platforms = ["LANDSAT_9", "LANDSAT_8"]
            collection = 'landsat-c2l2-sr'
            bands = ['coastal', 'blue', 'green', 'red', 'nir08', 'swir16', 'swir22', 'qa_pixel']
            pathkey = "landsat:wrs_path"
            rowkey = "landsat:wrs_row"
        elif sensor == 'S2':
            stack_server_url = 'https://earth-search.aws.element84.com/v1'
            platforms = ["sentinel-2a", "sentinel-2b"]
            collection = 'sentinel-2-l2a'
            bands = ['blue', 'coastal', 'green', 'nir', 'nir08', 'nir09', 'red', 'rededge1', 'rededge2', 'rededge3', 'swir16', 'swir22']
            pathkey = ""
            rowkey = ""
            
        query = {
            "eo:cloud_cover": {
            "gte": 0,
            "lte": cloud_cover
            },
            "platform": {
                "in": platforms
            },
            # "landsat:wrs_path": {
            #     "in": [144, 145, 146]
            # },
            # "landsat:wrs_row": {
            #     "in": [38, 39, 40]
            # }
        }
    
        aws_session = AWSSession(boto3.Session(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY), requester_pays=True)
        LandsatSTAC = Client.open(stack_server_url, headers=[])

        timeRange = f'{start_date}/{end_date}'

        LandsatSearch = LandsatSTAC.search( 
            intersects = aoi_geom,
            datetime = timeRange,
            query =  query,
            collections = [collection]
        )
        # print(aoi_geom)
        # return
        Landsat_items = [i.to_dict() for i in LandsatSearch.get_items()]
        print(f"{len(Landsat_items)} Landsat scenes fetched")
        # with open(
        #     f"scenes.json", "w"
        # ) as fp:
        #     json.dump(Landsat_items, fp)
    
        # bbox = bounds(aoi_geom)
    
        download_tasks = []

        for scene in Landsat_items:
            download_task = asyncio.ensure_future(
                DataDownloader.aync_download_scene(loop, scene, aoi_geom, sensor, params, bands, pathkey, rowkey)
            )
            download_tasks.append(download_task)
            # break
            # DataDownloader.download_scene(scene, aoi_geom, sensor, params, bands, pathkey, rowkey)
        
        responses = await asyncio.gather(*download_tasks)
        return responses


aoi_path = "/projects/gis-daemon/Ingestion/aoi/uk_boundary.json"
DataDownloader.for_geojson(aoi_path, {
    "start_date": '2016-01-01',
    "end_date":  '2016-12-31',
    "sensor": 'L8',
    "cloud_cover": 95,
    "rows_paths": [
        '144039',
        '145038',
        '145039',
        '145040',
        '146038',
        '146039'
    ]
})