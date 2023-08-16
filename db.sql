--
-- PostgreSQL database dump
--

-- Dumped from database version 12.15 (Ubuntu 12.15-0ubuntu0.20.04.1)
-- Dumped by pg_dump version 12.15 (Ubuntu 12.15-0ubuntu0.20.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;


--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: dataset_def; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dataset_def (
    dataset_id integer NOT NULL,
    ds_name character varying(500),
    ds_description character varying(500),
    no_of_bands integer,
    data_type character varying(500),
    def_color_scheme character varying(1000),
    band_meta text,
    is_querable boolean DEFAULT false,
    scale_factor double precision DEFAULT 1,
    value_offset double precision DEFAULT 0
);


ALTER TABLE public.dataset_def OWNER TO postgres;

--
-- Name: dataset_def_dataset_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dataset_def_dataset_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.dataset_def_dataset_id_seq OWNER TO postgres;

--
-- Name: dataset_def_dataset_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dataset_def_dataset_id_seq OWNED BY public.dataset_def.dataset_id;


--
-- Name: geo_processes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.geo_processes (
    id integer NOT NULL,
    pid character varying(250) DEFAULT ''::character varying,
    pname character varying(250) DEFAULT ''::character varying,
    status character varying(250) DEFAULT 'RUNNING'::character varying,
    pdata text DEFAULT ''::text,
    outputs text DEFAULT ''::text
);


ALTER TABLE public.geo_processes OWNER TO postgres;

--
-- Name: geo_processes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.geo_processes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.geo_processes_id_seq OWNER TO postgres;

--
-- Name: geo_processes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.geo_processes_id_seq OWNED BY public.geo_processes.id;


--
-- Name: ingest_master; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ingest_master (
    ingest_id integer NOT NULL,
    dataset_id integer,
    time_index bigint,
    geom public.geometry(Polygon,4326),
    date_time timestamp without time zone,
    created_on timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(500) DEFAULT 'admin'::character varying
);


ALTER TABLE public.ingest_master OWNER TO postgres;

--
-- Name: ingest_master_ingest_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ingest_master_ingest_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.ingest_master_ingest_id_seq OWNER TO postgres;

--
-- Name: ingest_master_ingest_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ingest_master_ingest_id_seq OWNED BY public.ingest_master.ingest_id;


--
-- Name: task_preview; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task_preview (
    id integer NOT NULL,
    task_data text,
    task_id character varying(75),
    aoi_code character varying(75)
);


ALTER TABLE public.task_preview OWNER TO postgres;

--
-- Name: task_preview_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.task_preview_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.task_preview_id_seq OWNER TO postgres;

--
-- Name: task_preview_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.task_preview_id_seq OWNED BY public.task_preview.id;


--
-- Name: tiles_local; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tiles_local (
    tile_id integer NOT NULL,
    ingest_id integer,
    dataset_id integer,
    zoom_level integer,
    time_index bigint,
    spatial_index_x integer,
    spatial_index_y integer,
    file_path character varying(500),
    created_on timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_by character varying(500) DEFAULT 'admin'::character varying,
    z_index character varying(500) DEFAULT '0'::character varying,
    sat_ref character varying(250) DEFAULT ''::character varying
);


ALTER TABLE public.tiles_local OWNER TO postgres;

--
-- Name: tiles_local_tile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tiles_local_tile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tiles_local_tile_id_seq OWNER TO postgres;

--
-- Name: tiles_local_tile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tiles_local_tile_id_seq OWNED BY public.tiles_local.tile_id;


--
-- Name: user_aoi; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_aoi (
    id integer NOT NULL,
    aoi_code character varying(500),
    geom public.geometry(Polygon,4326),
    aoi_name character varying(500) DEFAULT ''::character varying,
    is_temp boolean DEFAULT false
);


ALTER TABLE public.user_aoi OWNER TO postgres;

--
-- Name: user_aoi_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_aoi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_aoi_id_seq OWNER TO postgres;

--
-- Name: user_aoi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_aoi_id_seq OWNED BY public.user_aoi.id;


--
-- Name: dataset_def dataset_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dataset_def ALTER COLUMN dataset_id SET DEFAULT nextval('public.dataset_def_dataset_id_seq'::regclass);


--
-- Name: geo_processes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.geo_processes ALTER COLUMN id SET DEFAULT nextval('public.geo_processes_id_seq'::regclass);


--
-- Name: ingest_master ingest_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ingest_master ALTER COLUMN ingest_id SET DEFAULT nextval('public.ingest_master_ingest_id_seq'::regclass);


--
-- Name: task_preview id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_preview ALTER COLUMN id SET DEFAULT nextval('public.task_preview_id_seq'::regclass);


--
-- Name: tiles_local tile_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tiles_local ALTER COLUMN tile_id SET DEFAULT nextval('public.tiles_local_tile_id_seq'::regclass);


--
-- Name: user_aoi id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_aoi ALTER COLUMN id SET DEFAULT nextval('public.user_aoi_id_seq'::regclass);


--
-- Name: task_preview task_preview_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_preview
    ADD CONSTRAINT task_preview_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

