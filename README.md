# LISS-III ARDFramework
This repo contains the codes for creating the data cube based on the Indian LISS III sensor on Single Node. The instructions guides to create a sinlge compute node Spatial data cube.
The data folder contains the details of the data set used in the paper. The data folders have subfolders as input, reference, and output. The input folder contains the metadata of the input dataset. The reference folder has metadata of reference dataset. The output folder is where the processed output files get generated. The actual tiff images are not provided due to **GitHub lfs** storage quota constraints. These datasets can be asked by clicking the data set links requests.
The other folders contain set codes, which enable the installation of base software components  mentioned in the installation section to build the complete processing chain for the LISS-III sensor data sets.

## Pre-Installation preparation
Before installation Pre-installation preparation must be followed to build the enable the different components of framework.The frameworks requires the separate environment for each of the components. These environment are created using the analconda software.The environment files can be obtained by clonning this repo. These steps can be following in 3 pre-installtion steps given below.
1. Clone project directory 
 ```bash
  git clone https://github.com/ashutoshkumarjha/LISSARDFramework.git
 ```
 2. Download the [anaconda](https://enterprise-docs.anaconda.com/en/latest/)
 3. Follow the [instruction](http://docs.anaconda.com/anaconda/install)  to install.

## Installation
To create the Spatial data cube based on the LISS-III sensors based satellite imagery requires following steps. 
## > Installation of software components
The framework requires the creation of different software computational environment which contains the different component of processing frameworks. After successful installation of anaconda start different components installation. These components are 
### 1.1 ARCSI
The Atmospheric and Radiometric Correction of Satellite Imagery ([ARCSI](https://github.com/remotesensinginfo/arcsi))  does the atmospheric correction.
- Conda environment to run ARCSI library is created using the environment config file `./arcsi/arcsi.yml`
- Run the following command:
```sh
conda env create -f ./arcsi/arcsi.yml
```
- Once the environment is ready, activate the arcsi environment and install arcsi from git repository. This repo contains the modified code to enable the LISS-III sensors.
```sh
git clone https://github.com/ashutoshkumarjha/arcsi.git
cd arcsi
python setup.py install
```
- It will install the arcsi library to the local conda environment `arcsi`

### 1.2. AROSICS
The geometric correction module is Automated and Robust Open-Source Image Co-Registration Software for Multi-Sensor Satellite Data ([AROSIC]( https://pypi.org/project/arosics/) )
- Run the following command to create the `arosics` environment:
```sh
conda env create -f ./AROSICS/arosics.yml
```
### 1.3. Open Data Cube
The Open Data Cube ([ODC](https://pypi.org/project/arosics/)) is the third components which can organize the satellite data in a spatial data cube allowing the dicing and slicing of raster data in space and time domains.
- Run the following command to create the `odc` environment:
```sh
conda env create -f ./ODC/odc.yml
```
- Install Postgres database and create a database `datacube`
- Modify the database credentials and copy the `./ODC/.datacube.conf` to the `{HOME}./.odc/.datacube.conf` directory of the system.
- Activate the environment & initialize the database
```sh
conda activate odc
datacube -v system init
```
- Deactivate the environment
```sh
conda deactivate
```

## > Input dataset processing
The input folder contains date set including input and reference images organised in repective folders.
 The input files must be extracted in the input folder. e.g. L1 LISS III data `./data/input/1983747221/*` has details of input images used in this work.
The references folder has reference images used during co-registration. e.g. In this work used LandSat8 details are kept in `./data/references/LC08_L2SP_144039_20171118_20200902_02_T1`.

These data sets can be requested on using by clicking the Download link.
 - Download [[1983747221](https://drive.google.com/file/d/1U8t1mAN5XCBhAHdkCZpBVC-15PPyDOTK/view?usp=share_link),[1983747261](https://drive.google.com/file/d/1aY6KrjTp0oQJ91hQ1v5k94Ljzwt0NyoZ/view?usp=sharing)] (input LISS-III images) & extract into directories `./data/input/1983747221/` and `./data/input/1983747261/` 
 - Download Landsat-8-Reference images for given input images [[1983747221]](https://drive.google.com/file/d/1InpOK0q0B3gSNe2Ltth63gPG3uXaPjVe/view?usp=share_link),[1983747261](https://drive.google.com/file/d/1qOARxTaJkNz1CtArsmWurj98XYDvLQ9U/view?usp=share_link)] & copy or create symbolic link to the reference image to the `./data/input/1983747221/ref/` and `./data/input/references/1983747261/` directories.
 - Add empty directories `atm_corrected/1983747221` & `atm_corrected/1983747261` and `coreg/1983747221` & `coreg/1983747261`  inside `./data`  folder.
 - Sample directory structure corresponding to [1983747221](https://drive.google.com/file/d/1U8t1mAN5XCBhAHdkCZpBVC-15PPyDOTK/view?usp=share_link) is as shown below:
 ![alt text](./folder_struc.PNG)
## 2.1. Atmospheric Correction
- Activate the arcsi conda environment
```sh
conda activate arcsi
```
- Once the input images `BAND[2-5]` are downloaded into directories `./data/input/1983747221/`, `./data/input/1983747261/`run the following arcsi command to start atm correction module. It will generate .kea files for radiance, toa & surface reflectance values.
```sh
arcsi.py -s L3 -f KEA --stats -p RAD TOA SREF --aeropro NoAerosols --atmospro NoGaseousAbsorption --aot 0.5 -o "./data/atm_corrected/1983747221/" -i "./data/input/1983747221/BAND_META.txt"
```
- Reproject and convert the data into tiff file
```sh
gdalwarp -t_srs 'EPSG:7755' "./data/atm_corrected/1983747221/L3_20171120_latn812lone310_r49p99_vmsk_rad_sref.kea" "./data/atm_corrected/1983747221/L3_20171120_latn812lone310_r49p99_vmsk_rad_sref_7755.tif"
```
- Deactivate the environment
```sh
conda deactivate
```

## 2.2. Geometric Correction
- Activate the arosics environment
```sh
conda activate arosics
```
- Run the python script provided for image registration `img_reg.py`
```sh
python ./AROSICS/img_reg.py
```
- Deactivate the environment
```sh
conda deactivate
```

## 2.3. Data Ingestion to ODC
- Activate the odc environment
```sh
conda activate odc
```
- Generate `product.yml` (or modify & use the sample `./ODC/product.yml` provided) & add the product definition to the datacube (one time operation)
- A python script is provided to generate the product yaml file. Modify the content according to the sensor requirement and run the script `./ODC/generate_pdef.py`
```sh
python ./ODC/generate_pdef.py
```
- Add the product to the datacube
```sh
datacube product add ./ODC/product.yml
```
- Similarly, script for generating dataset yaml is provided `./ODC/generate_ds.py`. Modify and run the script. (or modify & use the sample `./ODC/dataset.yml` provided)
```sh
python ./ODC/generate_ds.py
```
- Add the dataset to the database
```sh
datacube dataset add ./ODC/dataset.yml
```
- Finally, ingest the added datasets using the provided, `./ODC/ingest.yml`. Please, make sure to update the ingestion directory in the yaml file.
```sh
datacube ingest -c ./ODC/ingest.yml
```
- Deactivate the environment
```sh
conda deactivate
```
## Notes
The use of DEM and modfication of arcsi input parameters can be used for better corrected output.