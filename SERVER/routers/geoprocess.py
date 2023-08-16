from fastapi import APIRouter
import time
from osgeo import ogr, osr
from starlette.responses import StreamingResponse
from db import Db
from sindexing import get_tile_intersection
from utils import tilenum2deg, get_tile_geom
from render import render_png, image_to_byte_array, render_png_multits
from pydantic import BaseModel
import asyncio
import subprocess
import threading
import os
import zipfile
from io import StringIO, BytesIO
import config as app_config
from ingestion import partition_data


class SubmitProcessReq(BaseModel):
    data: str
    name: str

class PreviewProcessReq(BaseModel):
    data: str
    aoi: str


config = app_config.config
router = APIRouter()


def run_sp(cmd_data, geo_data, name, pid):
    cmd_data.append(geo_data)
    cmd_data.append(pid)
    # /mnt/data/data_dir/tiles/
    # /mnt/data/data_dir/temp_data/
    # http://localhost:8080
    # /mnt/data/data_dir/geoprocess/
    # spark://10.128.0.17:7077
    cmd.append(config['tile_dir'])
    cmd.append(config['temp_dir'])
    cmd.append(config['server_url'])
    cmd.append(config['geoprocess_dir'])
    cmd.append(config['spark_master'])
    data = subprocess.Popen(cmd_data)
    output, error = data.communicate()
    print("-----------------GEOPROCESS_DONE-----------------")
    process_file = os.path.join(config["geoprocess_dir"], pid + ".out")
    with open(process_file) as f:
        process_out = f.readline()
    print(process_out)
    pid = Db.update_process_status(pid, "COMPLETED", process_out)
    
    print("Files: ", process_out.split(","))
    print("Ts: ", time.time())
    print("Sensor: ", "output_" + pid)
    print("Sat Ref: ", pid)

    ingest_files = process_out.split(",")
    start_ts = int(time.time()) - len(ingest_files) * 10
    sensor_name = "output_" + pid
    for i in range(len(ingest_files)):
        ingest_ts = (start_ts + (i * 10)) * 1000
        ingest_file = ingest_files[i]
        sat_ref = str(ingest_ts)
    
        partition_data(ingest_file, ingest_ts, sensor_name, sat_ref)

    print("-----------------GEOPROCESS_STATUS_UPDATED-----------------")
    print(output, error)
    return True


class GeoProcessThread(threading.Thread):
    def __init__(self, run_jar, geo_data, name, pid):
        threading.Thread.__init__(self)
        self.run_jar = run_jar
        self.geo_data = geo_data
        self.name = name
        self.pid = pid

    def run(self):
        print("Starting")
        run_sp(self.run_jar, self.geo_data, self.name, self.pid)
        print("Exiting ")


loop = asyncio.get_event_loop()


@router.post("/process/submit")
def submit_process(geoprocess: SubmitProcessReq):
    try:
        # Db.create_process(pname=geoprocess.name, pdata=geoprocess.data)
        pid = Db.create_process(pname=geoprocess.name, pdata=geoprocess.data)
        run_jar = [
            "java",
            "--add-opens=java.base/java.lang=ALL-UNNAMED",
            "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED",
            "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED",
            "--add-opens=java.base/java.io=ALL-UNNAMED",
            "--add-opens=java.base/java.net=ALL-UNNAMED",
            "--add-opens=java.base/java.nio=ALL-UNNAMED",
            "--add-opens=java.base/java.util=ALL-UNNAMED",
            "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED",
            "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED",
            "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED",
            "--add-opens=java.base/sun.nio.cs=ALL-UNNAMED",
            "--add-opens=java.base/sun.security.action=ALL-UNNAMED",
            "--add-opens=java.base/sun.util.calendar=ALL-UNNAMED",
            "--add-opens=java.security.jgss/sun.security.krb5=ALL-UNNAMED",
            "-cp",
            "/projects/data/project/geotrellis-spark-job-assembly-0.1.0.jar",
            "com.gishorizon.operations.WorkProcess",
        ]
        # run_jar = f' -cp geotrellis-spark-job-assembly-0.1.0.jar com.gishorizon.operations.WorkProcess '
        # run_jar += geoprocess.data
        download_thread = GeoProcessThread(
            run_jar, geoprocess.data, geoprocess.name, pid
        )
        # threading.Thread(
        #     target=run_sp, name="RunGeoProcess", args=(run_jar)
        # )
        download_thread.start()
        return {
            "message": "Success",
            "error": False,
            "data": f"ProcessId: {pid} started. Please, check the progress in task window",
        }
    except Exception as e:
        print(e)
        print("Failed due to exception")
        return None


@router.get("/process/getAll")
def get_all_process():
    try:
        processes = Db.get_processes()
        return {"message": "Success", "error": False, "data": processes}
    except Exception as e:
        print(e)
        print("Failed due to exception")
        return None


@router.get("/process/download")
def download_process_output(pid: str):
    try:
        process = Db.get_process_by_pid(pid)
        files = [v.strip() for v in process["outputs"].split(",")]
        return create_zipfile(files)
        # return {"message": "Success", "error": False, "data": process}
    except Exception as e:
        print(e)
        print("Failed due to exception")
        return None


def create_zipfile(filenames):
    zip_io = BytesIO()
    with zipfile.ZipFile(
        zip_io, mode="w", compression=zipfile.ZIP_DEFLATED
    ) as temp_zip:
        for fpath in filenames:
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(config["temp_dir"], fname)
            temp_zip.write(fpath, fname)
    return StreamingResponse(
        iter([zip_io.getvalue()]),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename=images.zip"},
    )



@router.post("/process/preview")
def download_process_output(geoprocess: PreviewProcessReq):
    try:
        aoi_code = geoprocess.aoi
        task_data = geoprocess.data
        pid = Db.create_task_preview(task_data, aoi_code)
        return {"message": "Success", "error": False, "data": pid}
    except Exception as e:
        print(e)
        print("Failed due to exception")
        return None
