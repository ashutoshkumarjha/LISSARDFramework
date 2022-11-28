from ruamel.yaml.main import round_trip_load as yaml_load, round_trip_dump as yaml_dump
from ruamel.yaml.comments import CommentedMap as OrderedDict, CommentedSeq as OrderedList
import uuid
from osgeo import gdal, osr
import argparse

parser = argparse.ArgumentParser()
 
parser.add_argument("-o", "--OUT_FILE", help = "Output yaml file path")
parser.add_argument("-id", "--INGEST_DIR", help = "Ingest directory")
parser.add_argument("-i", "--INPUT_FILE", help = "Input file")
args = parser.parse_args()

if(args.INGEST_DIR is None or args.OUT_FILE is None or args.INPUT_FILE is None):
    raise Exception('[Error] Invalid input.')


names=["Green", "Red", "VNIR", "SWIR"]
aliases=["Band_2", "Band_3", "Band_4", "Band_5"]

def get_ingst_ms(
    names=[],
    aliases=[]
):
    _t = []
    _idx = 0
    for name in names:
        _a = aliases[_idx]
        _t.append(get_ingst_ms_one(name=name, src_varname=name, alis=_a))
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

def generate_ingest_yaml(
    source_type = "LISS3",
    output_type = "Ingest_ARD_LISS3_ard",
    location = "",
    file_path_template = "L3_{tile_index[0]}_{tile_index[1]}_{start_time}.nc",
    description = "High Resolution Linear Imaging Self-Scanning System III",
    in_crs = 7755,
    tile_x = 23900,
    tile_y = 23900,
    res_x = 23.5,
    res_y = -23.5,
    measurements = []
):
    yaml_dict_file = OrderedDict({
        "id": str(uuid.uuid4()),
        "source_type": source_type,
        "output_type": output_type,
        "description": description,
        "file_path_template": file_path_template,
        "location": location,
        "global_attributes": OrderedDict({
            "title": "NRSC Datacube High Resolution Linear Imaging Self-Scanning System III",
            "summary": "High Resolution Linear Imaging Self-Scanning System III",
            "source": "IRS_P6 (LISS3 data is provided by the NRSC)",
            "institution": "NRSC",
            "instrument": "L3",
            "cdm_data_type": "Grid",
            "keywords": "AU/NRSC,NASA/GSFC/SED/ESD/IRS_P6,REFLECTANCE,LISS,EARTH SCIENCE",
            "keywords_vocabulary": "GCMD",
            "platform": "IRS_P6",
            "product_suite": "NRSC LISS3",
            "project": "AGDC",
            "coverage_content_type": "physicalMeasurement",
            "references": "http://www.gisat.cz/content/en/satellite-data/supplied-data/high-resolution?senzor=584#sat_detail",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "naming_authority": "NRSC",
            "acknowledgment": "LISS3 data is provided by the NRSC."
        }),
        "storage": OrderedDict({
            "driver": "NetCDF CF",
            "crs": "EPSG:" + str(in_crs),
            "tile_size": OrderedDict({
                "x": tile_x,
                "y": tile_y
            }),
            "resolution": OrderedDict({
                "x": res_x,
                "y": res_y
            }),
            "chunking": OrderedDict({
                "x": 20,
                "y": 20,
                "time": 1
            }),
            "dimension_order": ['time', 'y', 'x'],
        }),
        "fuse_data": "copy",
        "measurements": OrderedList(measurements),
        "allow_product_changes": True
    })
    with open(args.OUT_FILE, 'w') as file:
        yaml_dump(yaml_dict_file, file)

ds = gdal.Open(args.INPUT_FILE)
gt = ds.GetGeoTransform()
in_crs = int(osr.SpatialReference(wkt=ds.GetProjection()).GetAttrValue('AUTHORITY',1))

generate_ingest_yaml(
        source_type = "LISS3",
        output_type = "Ingest_ARD_LISS3_ard",
        location = args.INGEST_DIR,
        in_crs = 7755,
        res_x = 23.5,
        res_y = -23.5,
        measurements = get_ingst_ms(
            names=names,
            aliases=aliases
        )
    )