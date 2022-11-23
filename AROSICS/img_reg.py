import os
import sys
from arosics import COREG_LOCAL
from arosics import Tie_Point_Grid
path = '../data/'
scene='1983747221'
ard_img = path + '/ouput'+'/coreg/'+scene+'/corrected_7755.tif'
im_reference = path + '/references/LC08_L2SP_144039_20171118_20200902_02_T1_SR_B2_7755.TIF'
im_target = path + '/ouput'+ '/atm_corrected/L3_20171120_latn812lone310_r49p99_vmsk_rad_sref_7755.tif'
kwargs = {
      'grid_res'     : 200,
      'window_size'  : (64,64),
      'path_out'     : ard_img,
      'q'            : False,
}
CRL = COREG_LOCAL(im_reference,im_target,**kwargs)
tpoints = CRL.CoRegPoints_table
tpoints.to_csv(path + '/ouput'+'/tiepoints/'+scene+'_7755.csv')
CRL.correct_shifts()
os.system("gdal_translate -b 1 "+ard_img+" "+path+'output/coreg/'+scene+'/corrected_band_1.tif')
os.system("gdal_translate -b 2 "+ard_img+" "+path+'output/coreg/'+scene+'/corrected_band_2.tif')
os.system("gdal_translate -b 3 "+ard_img+" "+path+'output/coreg/'+scene+'/corrected_band_3.tif')
os.system("gdal_translate -b 4 "+ard_img+" "+path+'output/coreg/'+scene+'/corrected_band_4.tif')
print("ARD Creation Completed")
