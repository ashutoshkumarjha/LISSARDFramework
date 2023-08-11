
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
                user=config['db_user'],
                password=config['db_password'],
                host=config['db_host'],
                port="5432",
                database=config['db_database']
            )
        except Exception as error:
            print(error)
        return connection

    def get_db_dataset_def_by_id(dataset_id):
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select * from {config['tbl_dataset_def']}
                where dataset_id = '{dataset_id}'
                limit 1
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row

    def get_db_dataset_def_by_name(dataset_name):
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select * from {config['tbl_dataset_def']}
                where ds_name = '{dataset_name}'
                limit 1
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row


    def get_db_all_dataset_def():
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select * from {config['tbl_dataset_def']}
        """)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows
    
    def get_db_all_aoi_names():
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select aoi_code, id, aoi_name from user_aoi;
        """)
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
        if(from_ts is not None):
            qry += f" and date_time >= to_timestamp({from_ts/1000})::timestamp without time zone"
        if(to_ts is not None):
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
        if(from_ts is not None):
            qry += f" and ingest_master.date_time >= to_timestamp({from_ts/1000})::timestamp without time zone"
        if(to_ts is not None):
            qry += f" and ingest_master.date_time <= to_timestamp({to_ts/1000})::timestamp without time zone"
        cursor.execute(qry)
        for row in cursor:
            rows.append(row)
        cursor.close()
        conn.close()
        return rows
    
    def insert_aoi(aoi_name, aoi_gj):
        qry = f"""
            insert into user_aoi (
                aoi_code,
                geom,
                aoi_name
            )
            values (
                '{generate_string()}',
                st_setsrid(st_geomfromgeojson('{aoi_gj}'), 4326),
                '{aoi_name}'
            ) RETURNING aoi_code;
        """
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(qry)
        conn.commit()
        row = cursor.fetchone()['aoi_code']
        cursor.close()
        conn.close()
        return row

    def get_db_tile_by_zindex_zoom_ds(z_index, zoom_level, ds_id, x_index, y_index, tindex):
        rows = []
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select
                distinct ingest_id, dataset_id, time_index, file_path
            from {config['tbl_tiles']}
                where dataset_id={ds_id} and zoom_level={zoom_level} and z_index='{z_index}'
            ;
        """)
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
    
    def get_aoi_geom_by_aoi_code(aoi_code):
        conn = Db.get_db_conn()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(f"""
            select aoi_code, st_asgeojson(geom) as geom, st_asgeojson(st_envelope(geom)) as aoi_extent, aoi_name from user_aoi where aoi_code='{aoi_code}';
        """)
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