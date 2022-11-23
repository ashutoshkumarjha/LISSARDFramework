from ruamel.yaml.main import round_trip_load as yaml_load, round_trip_dump as yaml_dump
from ruamel.yaml.comments import CommentedMap as OrderedDict, CommentedSeq as OrderedList
import uuid
from osgeo import gdal, ogr, osr
import numpy as np
import math
import uuid
from pyproj import Transformer
from shapely import geometry

def get_ds_ms(
    names=[],
    datapaths=[]
):
    _t = OrderedDict({})
    _idx = 0
    for name in names:
        _p = datapaths[_idx]
        _t[name] = OrderedDict({"path":_p})
    return _t

def get_ingst_ms_one(
    name="",
    src_varname="",
    alis="",
    dtype="float32",
    nodata=0,
    resampling_method="cubic"
):
    return OrderedDict({
        "name": name,
        "dtype": dtype,
        "nodata": nodata,
        "resampling_method": "cubic",
        "src_varname": src_varname,
        "zlib": True,
        "complevel": 4,
        "shuffle": True,
        "fletcher32": False,
        "contiguous": False,
        "attrs": OrderedDict({"alias": alis})
    })

def generate_ds_properties(
    platform="IRS_P6",
    instrument="L3",
    dt="2017-11-20T 14:30:54.1476229Z",
    processing_datetime="2017-11-20Z",
    file_format="Geotiff",
    region_code="r51p99",
    dataset_maturity="final",
    product_family="ard"
):
    return OrderedDict({
            "eo:platform": platform,
            "eo:instrument": instrument,
            "datetime": dt,
            "odc:processing_datetime": processing_datetime,
            "odc:file_format": file_format,
            "odc:region_code": region_code,
            "dea:dataset_maturity": dataset_maturity,
            "odc:product_family": product_family
        })

def generate_ds_yaml(
    product_name = "LISS3",
    in_crs = 32644,
    shape = [],
    transform = [],
    measurements = OrderedDict({}),
    properties = OrderedDict({}),
):
    yaml_dict_file = OrderedDict({
        "id": str(uuid.uuid4()),
        "$schema": 'https://schemas.opendatacube.org/dataset',
        "product": OrderedDict({
            "name": product_name
        }),
        "crs": "EPSG:" + str(in_crs),
        "grids": OrderedDict({
            "default": OrderedDict({
                "shape": shape,
                "transform": transform
            })
        }),
        "measurements": measurements,
        "properties": properties,
        "lineage": {}
    })
    with open(r'./dataset.yaml', 'w') as file:
        yaml_dump(yaml_dict_file, file)

INPUT_DATA_ARR=["../output/coreg/1983747221/L3_20171120_latn805lone286_r51p99_vmsk_rad_sref.tif"]
FILE_PATH="../temp/data_"
names=["Green", "Red", "VNIR", "SWIR"]

for INPUT_DATA in INPUT_DATA_ARR:
    ds = gdal.Open(INPUT_DATA)
    gt = ds.GetGeoTransform()
    width = ds.RasterXSize
    height = ds.RasterYSize
    in_crs = int(osr.SpatialReference(wkt=ds.GetProjection()).GetAttrValue('AUTHORITY',1))

    _uid = str(uuid.uuid4())

    for b_no in range(0, ds.RasterCount):
        ods = gdal.Translate(FILE_PATH + _uid + "_" + str(b_no)  +'.tif', ds, bandList=[b_no+1])
        c_x = ods.RasterXSize
        c_y = ods.RasterYSize
        ogt = ods.GetGeoTransform()

    generate_ds_yaml(
        product_name = "LISS3",
        in_crs = in_crs,
        shape = [width, height],
        transform = [
            ogt[1],
            0,
            ogt[0],
            0,
            ogt[5],
            ogt[3],
            0,
            0,
            1
        ],
        measurements = get_ds_ms(
            names=names,
            datapaths=[FILE_PATH + _uid + "_0.tif", FILE_PATH + _uid + "_1.tif", FILE_PATH + _uid + "_2.tif", FILE_PATH + _uid + "_3.tif"]
        ),
        properties = generate_ds_properties()
    )
