import json
from DataIngestion import partition_data

inputs = json.load(open("ingestion-input.json"))



for i in inputs:
    meta_data = {}
    fname = i['tiePoints'].split('/')[-1].split('.')[0]
    with open(f'/projects/liss3/outputs/meta/{fname}.txt') as f:
        for line in f.readlines():
            _k = line.split('=')[0]
            if(_k in ["Path", "Row"]):
                meta_data[_k] = line.split('=')[1][1:-1]
    sat_ref = f'{meta_data["Path"]}{meta_data["Row"]}'
    partition_data(i["filePath"], i["ts"], i["sensor"], sat_ref)
