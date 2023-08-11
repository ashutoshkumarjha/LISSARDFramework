from osgeo import gdal, ogr, osr
import os
import osgeo
import json
from datetime import datetime
import math
import zCurve as z
import psycopg2
from psycopg2.extras import RealDictCursor
import config as app_config
from mpi4py import MPI


tiff_driver = gdal.GetDriverByName('GTiff')
shp_driver = ogr.GetDriverByName("ESRI Shapefile")
config = app_config.config

def get_db_conn():
    try:
        connection = psycopg2.connect(
            user=config['db_user'],
            password=config['db_password'],
            host=config['db_host'],
            port="5432",
            database=config['db_database']
        )
    except Exception as error:
        print(error)
    return connection

def add_db_ingestion(data):
    qry = f"""
        insert into ingest_master (
            dataset_id,
            time_index,
            geom,
            date_time
        )
        values (
            {data['dataset_id']},
            {data['time_index']},
            {data['geom']},
            {data['date_time']}
        ) RETURNING ingest_id;
    """
    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(qry)
    conn.commit()
    row = cursor.fetchone()['ingest_id']
    cursor.close()
    conn.close()
    # row = cursor.fetchone()
    return row

def add_db_tile(tile_data):
    qry = f"""
        insert into tiles_local(
            ingest_id,
            dataset_id,
            zoom_level,
            time_index,
            spatial_index_x,
            spatial_index_y,
            z_index,
            file_path
        )
        values (
            {tile_data['ingest_id']},
            {tile_data['dataset_id']},
            {tile_data['zoom_level']},
            {tile_data['time_index']},
            {tile_data['spatial_index_x']},
            {tile_data['spatial_index_y']},
            {tile_data['z_index']},
            {tile_data['file_path']}
        ) returning tile_id
    """
    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(qry)
    conn.commit()
    row = cursor.fetchone()['tile_id']
    cursor.close()
    conn.close()
    # row = cursor.fetchone()
    return row

def get_db_tile_by_z_index(dataset_id, z_index):
    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"""
        select * from tiles_local
            where dataset_id = '{dataset_id}' and z_index = {z_index}
            limit 10
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def update_db_tile_sat_ref(tile_id, sat_ref):
    conn = get_db_conn()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"""
        update tiles_local
            set sat_ref = '{sat_ref}'
            where tile_id = '{tile_id}';
    """)
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_db_dataset_def_by_name(dataset_name):
        conn = get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select * from {config['tbl_dataset_def']}
                where ds_name = '{dataset_name}'
                limit 1
        """)
        row = cursor.fetchone()
        return row

def get_extent_of_ds(dataset):
    geotransform = dataset.GetGeoTransform()
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    xmin = geotransform[0]
    ymax = geotransform[3]
    xmax = xmin + geotransform[1] * cols
    ymin = ymax + geotransform[5] * rows

    # print('Extent:', xmin, ymin, xmax, ymax)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xmin, ymin)
    ring.AddPoint(xmin, ymax)
    ring.AddPoint(xmax, ymax)
    ring.AddPoint(xmax, ymin)
    ring.AddPoint(xmin, ymin)

    geom = ogr.Geometry(ogr.wkbPolygon)
    geom.AddGeometry(ring)
    return geom


def reproject(geometry, in_srs, out_srs):
    src_srs = osr.SpatialReference()
    src_srs.ImportFromEPSG(in_srs)
    target_srs = osr.SpatialReference()
    if int(osgeo.__version__[0]) >= 3:
        target_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
        src_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
    target_srs.ImportFromEPSG(out_srs)
    transform = osr.CoordinateTransformation(src_srs, target_srs)
    # print(transform)
    geometry.Transform(transform)
    return geometry


def reproject_extent(xmin, ymin, xmax, ymax, in_srs, out_srs):
    src_srs = osr.SpatialReference()
    src_srs.ImportFromEPSG(in_srs)
    target_srs = osr.SpatialReference()
    if int(osgeo.__version__[0]) >= 3:
        target_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
        src_srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)
    target_srs.ImportFromEPSG(out_srs)
    transform = osr.CoordinateTransformation(src_srs, target_srs)

    input_geom = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xmin, ymin)
    ring.AddPoint(xmax, ymin)
    ring.AddPoint(xmax, ymax)
    ring.AddPoint(xmin, ymax)
    ring.AddPoint(xmin, ymin)
    input_geom.AddGeometry(ring)
    input_geom.AssignSpatialReference(src_srs)

    # Create a geometry transformer
    transformer = osr.CoordinateTransformation(src_srs, target_srs)

    # Transform the input geometry to the output SRS
    output_geom = input_geom.Clone()
    output_geom.Transform(transformer)

    # Get the transformed extent
    xmin, xmax, ymin, ymax = output_geom.GetEnvelope()
    return (xmin, ymin, xmax, ymax)

def partition_data(input_tiff, input_ts, sensor_name, sat_ref = None):
    start_ts = int(datetime.timestamp(datetime.strptime(config["start_time"], '%Y-%m-%d %H:%M:%S'))*1000)
    time_index = int((input_ts - start_ts)/1000)
    print(f"Saving tiles to {config['tile_dir']}, Sc:{input_tiff}, Ti:{time_index}")

    dataset = gdal.Open(input_tiff)
    if(dataset is None):
        print("No data")
        return False
    
    extent_geom = get_extent_of_ds(dataset)
    proj = osr.SpatialReference(wkt=dataset.GetProjection())
    src_src_code = 7755 #int(proj.GetAttrValue('AUTHORITY',1))
    extent_geom = reproject(extent_geom, src_src_code, 4326)
    extent_geom.FlattenTo2D()

    if(src_src_code!=4326):
        # print(f"Reprojecting: {src_src_code} -> {4326}")
        dataset = gdal.Warp('', dataset, format='VRT', dstSRS="EPSG:4326")
        # print(f"Reprojection completed")

    ds_def = get_db_dataset_def_by_name(sensor_name)
    ingest_data = {
        "dataset_id": ds_def["dataset_id"],
        "geom": f"st_setsrid(st_geomfromgeojson('{extent_geom.ExportToJson()}'), 4326)",
        "time_index": time_index,
        "date_time": f"to_timestamp('{input_ts/1000}')::timestamp without time zone"
    }
    ingest_id = add_db_ingestion(ingest_data)
    
    dir_path = config["tile_dir"]
    tindex_file = os.path.join(config["tindex_dir"], f"{sensor_name}.json")
    tile_size = 256

    tindex_data = {"data": []}
    if os.path.exists(tindex_file):
        tindex_data = json.load(open(tindex_file))
    
    tindex_data["data"].append(time_index)

    with open(tindex_file, "w") as tifile:
        tifile.write(json.dumps(tindex_data, indent=4))

    for i in range(4, 13):
        lcount = 0
        level_id = i
        filename = f"IndiaWGS84GCS{str(i)}.shp"
        shp_file = os.path.join(config["grid_dir"], filename)
        shp_ds = shp_driver.Open(shp_file)
        shp_lyr = shp_ds.GetLayer()

        aoi_extent = shp_lyr.GetExtent()
        # print(aoi_extent)
        aoi_extent = reproject_extent(aoi_extent[0], aoi_extent[2], aoi_extent[1], aoi_extent[3], 4326, 3857)
        fea_count = shp_lyr.GetFeatureCount()
        f_index = 0
        for feature in shp_lyr:
            geometry = feature.GetGeometryRef()
            spatial_partition_index = tuple(map(int, feature.GetField('id').replace('(','').replace(')','').split(',')))
            level_id = spatial_partition_index[2]
            x_id = spatial_partition_index[0]
            y_id = spatial_partition_index[1]
            if(geometry.Intersects(extent_geom)):
                lcount += 1
                _e = geometry.GetEnvelope()
                tile_extent = geometry.GetEnvelope() #reproject(geometry, 4326, src_src_code).GetEnvelope()
                xmin = tile_extent[0]
                ymin = tile_extent[2]
                xmax = tile_extent[1]
                ymax = tile_extent[3]
                rel_file_path = f"{sensor_name}/{level_id}/{x_id}/{y_id}/" + f"{time_index}.tif"
                tile_file_dir = os.path.join(dir_path, f"{sensor_name}/{level_id}/{x_id}/{y_id}/")
                if not os.path.exists(tile_file_dir):
                    os.makedirs(tile_file_dir)

                out_path = os.path.join(dir_path, rel_file_path)
                # print(out_path)
                tile_data = {
                    "ingest_id": ingest_id,
                    "dataset_id": ds_def["dataset_id"],
                    "zoom_level": i,
                    "time_index": time_index,
                    "spatial_index_x": x_id,
                    "spatial_index_y": y_id,
                    "z_index": f"'{z.interlace(time_index, y_id, x_id)}'",
                    "file_path": f"'{rel_file_path}'"
                }
                if sat_ref is None:
                    sat_ref = input_tiff.split('/')[-1].split('_')[2]
                # print("Sat Ref: ", sat_ref)
                tile_id = add_db_tile(tile_data)
                update_db_tile_sat_ref(tile_id, sat_ref)
                # print(tile_id)



                tmp_ds = gdal.Translate(out_path, dataset, width=tile_size, height=tile_size, format='COG', projWin = [xmin, ymax, xmax, ymin], outputSRS="EPSG:4326", projWinSRS="EPSG:4326", noData=0, resampleAlg='cubic')
                tmp_ds = None
                print(f"[Level {i}] {f_index}/{fea_count}" + f' Features, Total tiles: {lcount}', end='\r')
                # break
            f_index += 1
        # print(f"Level {i}: {lcount}")
        shp_ds = None
        # break



def repair_data(input_tiff, input_ts, sensor_name):
    start_ts = int(datetime.timestamp(datetime.strptime(config["start_time"], '%Y-%m-%d %H:%M:%S'))*1000)
    time_index = int((input_ts - start_ts)/1000)
    print(f"Saving tiles to {config['tile_dir']}, Sc:{input_tiff}, Ti:{time_index}")

    dataset = gdal.Open(input_tiff)
    if(dataset is None):
        return False
    
    extent_geom = get_extent_of_ds(dataset)
    proj = osr.SpatialReference(wkt=dataset.GetProjection())
    src_src_code = int(proj.GetAttrValue('AUTHORITY',1))
    extent_geom = reproject(extent_geom, src_src_code, 4326)
    extent_geom.FlattenTo2D()

    if(src_src_code!=4326):
        # print(f"Reprojecting: {src_src_code} -> {4326}")
        dataset = gdal.Warp('', dataset, format='VRT', dstSRS="EPSG:4326")
        # print(f"Reprojection completed")

    ds_def = get_db_dataset_def_by_name(sensor_name)
    ingest_data = {
        "dataset_id": ds_def["dataset_id"],
        "geom": f"st_setsrid(st_geomfromgeojson('{extent_geom.ExportToJson()}'), 4326)",
        "time_index": time_index,
        "date_time": f"to_timestamp('{input_ts/1000}')::timestamp without time zone"
    }
    ingest_id = 0 #add_db_ingestion(ingest_data)
    
    dir_path = config["tile_dir"]
    # tindex_file = os.path.join(config["tindex_dir"], f"{sensor_name}.json")
    tile_size = 256

    # tindex_data = {"data": []}
    # if os.path.exists(tindex_file):
    #     tindex_data = json.load(open(tindex_file))
    
    # tindex_data["data"].append(time_index)

    # with open(tindex_file, "w") as tifile:
    #     tifile.write(json.dumps(tindex_data, indent=4))

    for i in range(4, 12):
        lcount = 0
        level_id = i
        filename = f"IndiaWGS84GCS{str(i)}.shp"
        shp_file = os.path.join(config["grid_dir"], filename)
        shp_ds = shp_driver.Open(shp_file)
        shp_lyr = shp_ds.GetLayer()

        aoi_extent = shp_lyr.GetExtent()
        # print(aoi_extent)
        aoi_extent = reproject_extent(aoi_extent[0], aoi_extent[2], aoi_extent[1], aoi_extent[3], 4326, 3857)
        fea_count = shp_lyr.GetFeatureCount()
        f_index = 0
        for feature in shp_lyr:
            geometry = feature.GetGeometryRef()
            spatial_partition_index = tuple(map(int, feature.GetField('id').replace('(','').replace(')','').split(',')))
            level_id = spatial_partition_index[2]
            x_id = spatial_partition_index[0]
            y_id = spatial_partition_index[1]
            if(geometry.Intersects(extent_geom)):
                lcount += 1
                _e = geometry.GetEnvelope()
                tile_extent = geometry.GetEnvelope() #reproject(geometry, 4326, src_src_code).GetEnvelope()
                xmin = tile_extent[0]
                ymin = tile_extent[2]
                xmax = tile_extent[1]
                ymax = tile_extent[3]
                rel_file_path = f"{sensor_name}/{level_id}/{x_id}/{y_id}/" + f"{time_index}.tif"
                tile_file_dir = os.path.join(dir_path, f"{sensor_name}/{level_id}/{x_id}/{y_id}/")
                if not os.path.exists(tile_file_dir):
                    os.makedirs(tile_file_dir)

                out_path = os.path.join(dir_path, rel_file_path)
                # print(out_path)
                tile_data = {
                    "ingest_id": ingest_id,
                    "dataset_id": ds_def["dataset_id"],
                    "zoom_level": i,
                    "time_index": time_index,
                    "spatial_index_x": x_id,
                    "spatial_index_y": y_id,
                    "z_index": f"'{z.interlace(time_index, y_id, x_id)}'",
                    "file_path": f"'{rel_file_path}'"
                }
                sat_ref = input_tiff.split('/')[-1].split('_')[2]
                existing_tile = get_db_tile_by_z_index(ds_def["dataset_id"], f"'{z.interlace(time_index, y_id, x_id)}'")
                update_db_tile_sat_ref(existing_tile['tile_id'], sat_ref)
                # tile_id = add_db_tile(tile_data)
                # print(tile_id)

                

                # tmp_ds = gdal.Translate(out_path, dataset, width=tile_size, height=tile_size, format='COG', projWin = [xmin, ymax, xmax, ymin], outputSRS="EPSG:4326", projWinSRS="EPSG:4326", noData=0, resampleAlg='cubic')
                # tmp_ds = None
                print(f"[Level {i}] {f_index}/{fea_count}" + f' Features, Total tiles: {lcount}', end='\r')
            f_index += 1
        # print(f"Level {i}: {lcount}")
        shp_ds = None




BASE_PATH = "/projects/data/project"

# comm = MPI.COMM_WORLD
# rank = comm.Get_rank()
# name = MPI.Get_processor_name()
# nprocs = comm.Get_size()


# def split(a, n):
#     k, m = divmod(len(a), n)
#     return list(a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))

# send_data = []

# if rank == 0:
#     print("Parsing params...", name, rank)
#     i = 0
#     tasks = []
#     for f in os.listdir(BASE_PATH):
#         i += 1
#         fpath = os.path.join(BASE_PATH, f"{f}/{f}.tif")
#         meta_path = os.path.join(BASE_PATH, f"{f}/meta.txt")
#         if os.path.exists(fpath) and os.path.exists(meta_path):
#             meta = json.load(open(meta_path))
#             # print(meta["srcPath"])
#             tasks.append([meta["srcPath"], meta["dateTime"], "Landsat_OLI"])
#             # partition_data()
#         # print("-----Done-----", i)

#     send_data = split(tasks, nprocs)
# else:
#     print("Other node", name, rank)
#     send_data = None

# in_datas = comm.scatter(send_data)

# print("Do work with the data", len(in_datas), name, rank)

# i = 0
# for d in in_datas:
#     partition_data(d[0], d[1], d[2])
#     print(name, rank, i)
#     i += 1

#mpiexec -machinefile /projects/gis-daemon/Ingestion/machinefile -n 1 -x LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH /home/mani/venv/gisenv/bin/python /projects/gis-daemon/Ingestion/DataIngestion.py