import os
import subprocess
import glob
import argparse

#SAMPLE CMD
# > python main.py -ap NoAerosols -atp NoGaseousAbsorption -ind /projects/mtech_project/sample_data/1983747221 -r /projects/mtech_project/sample_data/1983747221/ref/LC08_L2SP_144039_20171118_20200902_02_T1_SR_B2.TIF -aot 0.5 -igd /projects/mtech_project/sample_data/ingest_dir


parser = argparse.ArgumentParser()
 
parser.add_argument("-ind", "--INPUT_DATA_DIR", help = "Input data path")
parser.add_argument("-cod", "--COREG_DIR", help = "Coreg directory")
parser.add_argument("-atd", "--ATM_DIR", help = "Atm correction directory")
parser.add_argument("-r", "--REF_IMG", help = "Reference image")
parser.add_argument("-aot", "--AOT", help = "AOT value")
parser.add_argument("-ap", "--AEROPRO", help = "Aerosol profile")
parser.add_argument("-atp", "--ATMOSPRO", help = "AOT value")
parser.add_argument("-igd", "--INGEST_DIR", help = "Ingest directory")
args = parser.parse_args()

if(
    args.INPUT_DATA_DIR is None
        or args.REF_IMG is None
        or args.AOT is None
        or args.INGEST_DIR is None
        or args.AEROPRO is None
        or args.ATMOSPRO is None
        or args.COREG_DIR is None
        or args.ATM_DIR is None
    ):
    raise Exception('Invalid Params/Input')

#params
INPUT_DIR = args.INPUT_DATA_DIR #'data/input/1983747221/'
REF_IMG = args.REF_IMG #'data/references/1983747221/LC08_L2SP_144039_20171118_20200902_02_T1_SR_B2.TIF'
AOT_VALUE = float(args.AOT) #0.5
INGEST_DIR = args.INGEST_DIR #'data/output/1983747221'
AEROPRO = args.AEROPRO #NoAerosols
ATMOSPRO = args.ATMOSPRO #NoGaseousAbsorption

COREG_DIR = args.COREG_DIR #os.path.join(os.getcwd(), 'data/output/coreg/')
ATM_DIR = args.ATM_DIR #os.path.join(os.getcwd(), 'data/output/atm_corrected/')
meta_file = os.path.join(os.getcwd(), INPUT_DIR, 'BAND_META.txt')


def mk_dir(pt):
    if not os.path.exists(pt):
        os.makedirs(pt)

def get_sref_file(pt):
    for fname in glob.glob(pt + "*_sref.kea"):
        return fname
    return None


mk_dir(COREG_DIR)
mk_dir(ATM_DIR)


def run_sprocess(cmd):
    process = subprocess.Popen(
        (cmd).split(), stdout=subprocess.PIPE
    )
    output, error = process.communicate()
    print(output)

#ATM CORRECTION
run_sprocess('conda run -n arcsi arcsi.py -s L3 -f KEA --stats -p RAD TOA SREF --aeropro ' + AEROPRO + ' --atmospro ' + ATMOSPRO + ' --aot '+str(AOT_VALUE)+' -o '+ATM_DIR+' -i '+meta_file+'')
sref_kea = get_sref_file(os.path.join(os.getcwd(), ATM_DIR))
if(sref_kea is None):
    raise Exception('[Error] SREF')
print(sref_kea)

#REPROJECT
sref_tif_7755 = sref_kea + '_7755.tif'
run_sprocess('conda run -n arcsi gdalwarp -t_srs EPSG:7755 '+sref_kea+' ' + sref_tif_7755)
REF_IMG_7755 = REF_IMG + '_7755.tif'
run_sprocess('conda run -n arcsi gdalwarp -t_srs EPSG:7755 '+REF_IMG+' ' + REF_IMG_7755)

#COREG
sref_coreg = os.path.join(COREG_DIR, 'coreg.tif')
run_sprocess('conda run -n arosics python arosics/img_reg.py -cod '+COREG_DIR+' -i ' + sref_tif_7755 + ' -r ' + REF_IMG_7755 + ' -o ' + sref_coreg)
band_files = [
    os.path.join(COREG_DIR,"corrected_band_1.tif"),
    os.path.join(COREG_DIR,"corrected_band_2.tif"),
    os.path.join(COREG_DIR,"corrected_band_3.tif"),
    os.path.join(COREG_DIR,"corrected_band_4.tif")
]

#ODC DATASET
ds_yml = os.path.join(COREG_DIR,"ds.yml")
run_sprocess('conda run -n odc python generate_ds.py -i '+','.join(item for item in band_files)+' -o ' + ds_yml + ' -m ' + meta_file)
run_sprocess('conda run -n odc datacube dataset add '+ds_yml)

#INGEST
igst_yml = os.path.join(COREG_DIR,"ingest.yml")
run_sprocess('conda run -n odc python generate_ingest.py -o '+igst_yml+' -id '+INGEST_DIR+' -i ' + sref_coreg)
run_sprocess('conda run -n odc datacube ingest -c '+igst_yml)

#TODO: DEM COR
#gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -co NUM_THREADS=ALL_CPUS --config GDAL_CACHEMAX 1536 -wm 1536 -rpc -to RPC_DEM=${DEM_FILE} -of GTiff ${inFile} ${outFile}

# gdalwarp -multi -wo NUM_THREADS=ALL_CPUS -co NUM_THREADS=ALL_CPUS --config GDAL_CACHEMAX 1536 -wm 1536 -rpc -to RPC_DEM=./data/dem/r049p99.tif -of GTiff ./data/input/1983747221/BAND2.tif ./data/input/1983747221/BAND2_dem_cor.tif