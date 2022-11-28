from ruamel.yaml.main import round_trip_load as yaml_load, round_trip_dump as yaml_dump
from ruamel.yaml.comments import CommentedMap as OrderedDict, CommentedSeq as OrderedList
import uuid
from osgeo import gdal, ogr, osr
import argparse

parser = argparse.ArgumentParser()
 
parser.add_argument("-o", "--OUT_FILE", help = "Output yaml file path")
parser.add_argument("-i", "--BANDS", help = "List of band file paths")
parser.add_argument("-m", "--BAND_META", help = "Meta file")
args = parser.parse_args()

if(args.BANDS is None or args.OUT_FILE is None or args.BAND_META is None):
    raise Exception('[Error] Invalid input.')

OUT_FILE = args.OUT_FILE
BAND_META = args.BAND_META
IN_BANDS = [item for item in args.BANDS.split(',')]

names=["Green", "Red", "VNIR", "SWIR"]

m_params = ['ProductSceneEndTime', 'SceneEndTime', 'Path', 'Row']
meta_data = {}
with open(BAND_META) as f:
    for line in f.readlines():
        _k = line.split('=')[0]
        if(_k in m_params):
            meta_data[_k] = line.split('=')[1][1:-1]
print(meta_data)

def get_ds_ms(
    names=[],
    datapaths=[]
):
    _t = OrderedDict({})
    _idx = 0
    for name in names:
        _p = datapaths[_idx]
        _t[name] = OrderedDict({"path":_p})
        _idx = _idx + 1
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
    dt="",
    processing_datetime="",
    file_format="Geotiff",
    region_code="",
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
    with open(OUT_FILE, 'w') as file:
        yaml_dump(yaml_dict_file, file)

ds = gdal.Open(IN_BANDS[0])
gt = ds.GetGeoTransform()
width = ds.RasterXSize
height = ds.RasterYSize
in_crs = int(osr.SpatialReference(wkt=ds.GetProjection()).GetAttrValue('AUTHORITY',1))

_uid = str(uuid.uuid4())

generate_ds_yaml(
    product_name = "LISS3",
    in_crs = in_crs,
    shape = [width, height],
    transform = [
        gt[1],
        0,
        gt[0],
        0,
        gt[5],
        gt[3],
        0,
        0,
        1
    ],
    measurements = get_ds_ms(
        names=names,
        datapaths=IN_BANDS
    ),
    properties = generate_ds_properties(dt=meta_data['ProductSceneEndTime'], processing_datetime=meta_data['SceneEndTime'], region_code='r' + meta_data['Row']+'p'+meta_data['Path'])
)