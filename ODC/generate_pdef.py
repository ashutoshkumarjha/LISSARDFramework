from ruamel.yaml.main import round_trip_load as yaml_load, round_trip_dump as yaml_dump
from ruamel.yaml.comments import CommentedMap as OrderedDict, CommentedSeq as OrderedList
import uuid


def generate_product_mss(
    names=[],
    aliases=[],
    dtype='float32',
    nodata=0,
    units='reflectance'
):
    _t = []
    _idx = 0
    for name in names:
        _a = aliases[_idx]
        _t.append(generate_product_ms(name=name, alis=_a, dtype=dtype, nodata=nodata, units=units))
    return _t

def generate_product_ms(
    name="", alis="", dtype="", nodata=0, units=""
):
    return OrderedDict({
        "name": name,
        "aliases": [alis],
        "dtype": dtype,
        "nodata": nodata,
        "units": units
    })

def generate_product_yaml(
    name = "LISS3",
    description = "Resourcesat-1 LISS-III Data",
    metadata_type = "eo3",
    measurements = []
):
    yaml_dict_file = OrderedDict({
        "name": name,
        "description": description,
        "metadata_type": metadata_type,
        "metadata": OrderedDict({
            "product": OrderedDict({
                "name": name
            })
        }),
        "measurements": measurements
    })
    with open(r'./product.yaml', 'w') as file:
        yaml_dump(yaml_dict_file, file)


names=["Green", "Red", "VNIR", "SWIR"]
aliases=["Band_2", "Band_3", "Band_4", "Band_5"]

generate_product_yaml(
    name = "LISS3",
    description = "Resourcesat-1 LISS-III Data",
    metadata_type = "eo3",
    measurements=generate_product_mss(
        names=names,
        aliases=aliases,
        dtype='float32',
        nodata=0,
        units="reflectance"
    )
)