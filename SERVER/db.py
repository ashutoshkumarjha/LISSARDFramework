import json
from psycopg2.extras import RealDictCursor
import psycopg2
import config as app_config
from utils import generate_string

config = app_config.config


class Db:
    def get_db_conn():
        try:
            connection = psycopg2.connect(
                user=config["db_user"],
                password=config["db_password"],
                host=config["db_host"],
                port="5432",
                database=config["db_database"],
            )
        except Exception as error:
            print(error)
        return connection

    def get_db_dataset_def_by_id(dataset_id):
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select * from {config['tbl_dataset_def']}
                where dataset_id = '{dataset_id}'
                limit 1
        """
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def get_db_dataset_def_by_name(dataset_name):
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select * from {config['tbl_dataset_def']}
                where ds_name = '{dataset_name}'
                limit 1
        """
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def get_db_all_dataset_def():
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select * from {config['tbl_dataset_def']}
        """
        )
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows

    def get_db_all_aoi_names():
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select aoi_code, id, aoi_name from user_aoi;
        """
        )
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows

    def get_time_indexes_for_ds(dataset_id, from_ts, to_ts):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                distinct ingest_id, dataset_id, time_index, date_time
            from {config['tbl_ingest']}
                where dataset_id={dataset_id}
        """
        if from_ts is not None:
            qry += f" and date_time >= to_timestamp({from_ts/1000})::timestamp without time zone"
        if to_ts is not None:
            qry += f" and date_time <= to_timestamp({to_ts/1000})::timestamp without time zone"
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows

    def get_time_indexes_for_ds_aoi(aoi_code, dataset_id, from_ts, to_ts):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            with aoi as
            (
                select ST_Envelope(geom) as geom from user_aoi where aoi_code='{aoi_code}'
            )
            select ingest_master.ingest_id, ingest_master.dataset_id, ingest_master.time_index, ingest_master.date_time from ingest_master, aoi
            where st_intersects(ingest_master.geom, aoi.geom) and ingest_master.dataset_id={dataset_id}
        """
        # print(qry)
        if from_ts is not None:
            qry += f" and ingest_master.date_time >= to_timestamp({from_ts/1000})::timestamp without time zone"
        if to_ts is not None:
            qry += f" and ingest_master.date_time <= to_timestamp({to_ts/1000})::timestamp without time zone"
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows

    def insert_aoi(aoi_name, aoi_gj, is_temp):
        qry = f"""
            insert into user_aoi (
                aoi_code,
                geom,
                aoi_name,
                is_temp
            )
            values (
                '{generate_string()}',
                st_setsrid(st_geomfromgeojson('{aoi_gj}'), 4326),
                '{aoi_name}',
                {is_temp}
            ) RETURNING aoi_code;
        """
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(qry)
        conn.commit()
        row = cursor.fetchone()["aoi_code"]
        cursor.close()
        conn.close()
        return row

    def get_db_tile_by_zindex_zoom_ds(
        z_index, zoom_level, ds_id, x_index, y_index, tindex
    ):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select
                distinct ingest_id, dataset_id, time_index, file_path, sat_ref
            from {config['tbl_tiles']}
                where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
            ;
        """
        )
        # print(f"""
        #     select
        #         distinct ingest_id, dataset_id, time_index, file_path, sat_ref
        #     from {config['tbl_tiles']}
        #         where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
        #     ;
        # """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    
    
    def get_db_tile_by_zindex_zoom_dses(
        z_indexes, zoom_level, ds_id
    ):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select
                distinct ingest_id, dataset_id, time_index, file_path, sat_ref
            from {config['tbl_tiles']}
                where dataset_id={ds_id} and zoom_level={zoom_level} and z_index in ('{"','".join(z_indexes)}')
            ;
        """
        )
        # print(f"""
        #     select
        #         distinct ingest_id, dataset_id, time_index, file_path, sat_ref
        #     from {config['tbl_tiles']}
        #         where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
        #     ;
        # """)
        rows = []
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows
    def get_db_tile_by_zindex_zoom_dsesxy(
        x_indexes, y_indexes, t_indexes, zoom_level, ds_id
    ):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select
                distinct ingest_id, dataset_id, time_index, file_path, sat_ref
            from {config['tbl_tiles']}
                where dataset_id={ds_id} and zoom_level={zoom_level} and x_index in ({",".join(x_indexes)}) and y_index in ({",".join(y_indexes)}) and time_index in ({",".join(t_indexes)})
            ;
        """
        )
        # print(f"""
        #     select
        #         distinct ingest_id, dataset_id, time_index, file_path, sat_ref
        #     from {config['tbl_tiles']}
        #         where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
        #     ;
        # """)
        rows = []
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows
    
    def get_db_tile_by_zindex_zoom_ds_distinct(
        z_indexes, zoom_level, ds_id, x_index, y_index, tindexes
    ):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                distinct on (dataset_id, sat_ref) ingest_id, dataset_id, sat_ref, time_index, file_path
            from {config['tbl_tiles']}
                where dataset_id={ds_id} and zoom_level={zoom_level}
        """
        # print(z_indexes)
        qry += " and z_index in ('" + "','".join(z_indexes) + "')"
        qry += " and time_index in ('" + "','".join(tindexes) + "')"
        qry += " order by dataset_id, sat_ref, time_index;"
        # print(qry)
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows
        # return None
    
    def get_db_tile_by_zindex_zoom_outds_distinct(
        z_indexes, zoom_level, x_index, y_index, tindexes
    ):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                distinct on (dataset_id, sat_ref) ingest_id, dataset_id, sat_ref, time_index, file_path
            from {config['tbl_tiles']}
                where dataset_id=-1 and zoom_level={zoom_level}
        """
        # print(z_indexes)
        qry += " and z_index in ('" + "','".join(z_indexes) + "')"
        qry += " and time_index in ('" + "','".join(tindexes) + "')"
        qry += " order by dataset_id, sat_ref, time_index;"
        # print(qry)
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows
    
    def get_time_indexes_for_ds_aoi_out(output_name):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select distinct time_index from tiles_local where file_path like '{output_name}%';
        """
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows

    def get_db_tile_by_zindex_zoom_ds_sat_ref(
        z_index, zoom_level, ds_id, x_index, y_index, tindex, sat_refs
    ):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                distinct ingest_id, dataset_id, time_index, file_path, sat_ref
            from {config['tbl_tiles']}
                where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
        """
        if len(sat_refs) > 0:
            qry += " and sat_ref not in ('" + "','".join(sat_refs) + "');"
        cursor.execute(qry)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def get_aoi_geom_by_aoi_code(aoi_code):
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            f"""
            select aoi_code, st_asgeojson(geom) as geom, st_asgeojson(st_envelope(geom)) as aoi_extent, aoi_name from user_aoi where aoi_code='{aoi_code}';
        """
        )
        row = cursor.fetchone()

        # print(f"""
        #     select
        #         distinct ingest_id, dataset_id, time_index
        #     from {config['tbl_tiles']}
        #         where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
        #     ;
        # """, x_index, y_index, tindex)
        # for row in cursor:
        #     rows.append(row)
        cursor.close()
        conn.close()
        return row

    def create_process(pname, pdata):
        qry = f"""
            insert into geo_processes (
                pid,
                pname,
                pdata,
                status
            )
            values (
                '{generate_string()}',
                '{pname}',
                '{pdata}',
                'RUNNING'
            ) RETURNING pid;
        """
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(qry)
        conn.commit()
        row = cursor.fetchone()["pid"]
        cursor.close()
        conn.close()
        return row

    def update_process_status(pid, status, process_out):
        qry = f"""
            update geo_processes set status = '{status}', outputs = '{process_out}'
            where pid='{pid}' RETURNING pid;
        """
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(qry)
        conn.commit()
        row = cursor.fetchone()["pid"]
        cursor.close()
        conn.close()
        return row

    def get_processes():
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                *
            from geo_processes;
        """
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows

    def get_process_by_pid(pid):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                *
            from geo_processes where pid='{pid}';
        """
        cursor.execute(qry)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def create_task_preview(task_data, aoi_code):
        qry = f"""
            insert into task_preview (
                task_id, task_data, aoi_code
            )
            values (
                '{generate_string()}',
                '{task_data}',
                '{aoi_code}'
            ) RETURNING task_id;
        """
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(qry)
        conn.commit()
        row = cursor.fetchone()["task_id"]
        cursor.close()
        conn.close()
        return row

    def get_task_preview_by_tid(tid):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        qry = f"""
            select
                *
            from task_preview where task_id='{tid}';
        """
        cursor.execute(qry)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
