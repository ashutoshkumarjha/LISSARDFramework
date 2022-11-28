import os
import sys
import argparse
from arosics import COREG_LOCAL
from arosics import Tie_Point_Grid


parser = argparse.ArgumentParser()
 
parser.add_argument("-cod", "--COREG_DIR", help = "Working Directory")
parser.add_argument("-o", "--ARD_IMG", help = "Output image")
parser.add_argument("-i", "--TARGET_IMG", help = "Target image")
parser.add_argument("-r", "--REF_IMG", help = "Reference image")
args = parser.parse_args()

COREG_DIR = args.COREG_DIR
ARD_IMG = args.ARD_IMG
REF_IMG = args.REF_IMG
TARGET_IMG = args.TARGET_IMG

if(COREG_DIR is None or ARD_IMG is None or REF_IMG is None or TARGET_IMG is None):
      raise Exception('[Error] Invalid params')
kwargs = {
      'grid_res'     : 200,
      'window_size'  : (64,64),
      'path_out'     : ARD_IMG,
      'q'            : False,
}
CRL = COREG_LOCAL(REF_IMG, TARGET_IMG, **kwargs)
tpoints = CRL.CoRegPoints_table
tpoints.to_csv(os.path.join(COREG_DIR, 'tie_points_7755.csv'))
CRL.correct_shifts()
os.system("gdal_translate -b 1 "+ARD_IMG+" "+os.path.join(COREG_DIR,"corrected_band_1.tif"))
os.system("gdal_translate -b 2 "+ARD_IMG+" "+os.path.join(COREG_DIR,"corrected_band_2.tif"))
os.system("gdal_translate -b 3 "+ARD_IMG+" "+os.path.join(COREG_DIR,"corrected_band_3.tif"))
os.system("gdal_translate -b 4 "+ARD_IMG+" "+os.path.join(COREG_DIR,"corrected_band_4.tif"))
print("ARD Creation Completed")