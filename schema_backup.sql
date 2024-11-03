--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0
-- Dumped by pg_dump version 17.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: asset; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.asset (
    id integer DEFAULT 0 NOT NULL,
    building_id integer NOT NULL,
    property_type_id integer NOT NULL,
    floor integer,
    square_meters real,
    rooms integer,
    parcel_num text NOT NULL
);


ALTER TABLE public.asset OWNER TO postgres;

--
-- Name: building; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.building (
    id integer NOT NULL,
    neighborhood_id integer,
    parcel_num text NOT NULL,
    address text,
    total_floors integer,
    year_built integer
);


ALTER TABLE public.building OWNER TO postgres;

--
-- Name: city; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.city (
    id integer NOT NULL,
    name text NOT NULL,
    county_id integer NOT NULL,
    council_id integer NOT NULL
);


ALTER TABLE public.city OWNER TO postgres;

--
-- Name: council; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.council (
    id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.council OWNER TO postgres;

--
-- Name: county; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.county (
    id integer NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.county OWNER TO postgres;

--
-- Name: neighborhood; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.neighborhood (
    id integer NOT NULL,
    name text NOT NULL,
    city_id integer NOT NULL
);


ALTER TABLE public.neighborhood OWNER TO postgres;

--
-- Name: property_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.property_type (
    name text NOT NULL,
    id integer NOT NULL
);


ALTER TABLE public.property_type OWNER TO postgres;

--
-- Name: property_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.property_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.property_type_id_seq OWNER TO postgres;

--
-- Name: property_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.property_type_id_seq OWNED BY public.property_type.id;


--
-- Name: sales; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sales (
    asset_id integer NOT NULL,
    sale_date date NOT NULL,
    amount real NOT NULL,
    price_per_sqm real,
    trend_rate real,
    trend_years integer,
    parcel_num text,
    id integer NOT NULL,
    city_id integer
);


ALTER TABLE public.sales OWNER TO postgres;

--
-- Name: sales_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sales_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sales_id_seq OWNER TO postgres;

--
-- Name: sales_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sales_id_seq OWNED BY public.sales.id;


--
-- Name: property_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.property_type ALTER COLUMN id SET DEFAULT nextval('public.property_type_id_seq'::regclass);


--
-- Name: sales id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales ALTER COLUMN id SET DEFAULT nextval('public.sales_id_seq'::regclass);


--
-- Name: asset asset_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset
    ADD CONSTRAINT asset_pkey PRIMARY KEY (id, parcel_num);


--
-- Name: building building_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.building
    ADD CONSTRAINT building_pkey PRIMARY KEY (id, parcel_num);


--
-- Name: city city_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_name_key UNIQUE (name);


--
-- Name: city city_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city
    ADD CONSTRAINT city_pkey PRIMARY KEY (id);


--
-- Name: council council_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.council
    ADD CONSTRAINT council_name_key UNIQUE (name);


--
-- Name: council council_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.council
    ADD CONSTRAINT council_pkey PRIMARY KEY (id);


--
-- Name: county county_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.county
    ADD CONSTRAINT county_name_key UNIQUE (name);


--
-- Name: county county_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.county
    ADD CONSTRAINT county_pkey PRIMARY KEY (id);


--
-- Name: neighborhood neighborhood_name_city_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.neighborhood
    ADD CONSTRAINT neighborhood_name_city_id_key UNIQUE (name, city_id);


--
-- Name: neighborhood neighborhood_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.neighborhood
    ADD CONSTRAINT neighborhood_pkey PRIMARY KEY (id);


--
-- Name: property_type property_type_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.property_type
    ADD CONSTRAINT property_type_name_key UNIQUE (name);


--
-- Name: property_type property_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.property_type
    ADD CONSTRAINT property_type_pkey PRIMARY KEY (id);


--
-- Name: sales sales_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_pkey PRIMARY KEY (id);


--
-- Name: idx_asset_building; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_asset_building ON public.asset USING btree (building_id);


--
-- Name: idx_asset_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_asset_type ON public.asset USING btree (property_type_id);


--
-- Name: idx_building_neighborhood; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_building_neighborhood ON public.building USING btree (neighborhood_id);


--
-- Name: idx_building_parcel; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_building_parcel ON public.building USING btree (parcel_num);


--
-- Name: idx_city_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_city_name ON public.city USING btree (name);


--
-- Name: idx_council_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_council_name ON public.council USING btree (name);


--
-- Name: idx_county_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_county_name ON public.county USING btree (name);


--
-- Name: idx_neighborhood_city; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_neighborhood_city ON public.neighborhood USING btree (city_id);


--
-- Name: idx_sales_asset_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sales_asset_date ON public.sales USING btree (asset_id, sale_date);


--
-- Name: idx_sales_city_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sales_city_id ON public.sales USING btree (city_id);


--
-- Name: idx_sales_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sales_date ON public.sales USING btree (sale_date);


--
-- Name: asset asset_building_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset
    ADD CONSTRAINT asset_building_id_fkey FOREIGN KEY (building_id, parcel_num) REFERENCES public.building(id, parcel_num);


--
-- Name: asset asset_property_type_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.asset
    ADD CONSTRAINT asset_property_type_id_fkey FOREIGN KEY (property_type_id) REFERENCES public.property_type(id);


--
-- Name: building building_neighborhood_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.building
    ADD CONSTRAINT building_neighborhood_id_fkey FOREIGN KEY (neighborhood_id) REFERENCES public.neighborhood(id);


--
-- Name: city fk_council; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city
    ADD CONSTRAINT fk_council FOREIGN KEY (council_id) REFERENCES public.council(id);


--
-- Name: city fk_county; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.city
    ADD CONSTRAINT fk_county FOREIGN KEY (county_id) REFERENCES public.county(id);


--
-- Name: sales fk_sales_city; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT fk_sales_city FOREIGN KEY (city_id) REFERENCES public.city(id);


--
-- Name: neighborhood neighborhood_city_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.neighborhood
    ADD CONSTRAINT neighborhood_city_id_fkey FOREIGN KEY (city_id) REFERENCES public.city(id);


--
-- Name: sales sales_asset_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sales
    ADD CONSTRAINT sales_asset_fkey FOREIGN KEY (asset_id, parcel_num) REFERENCES public.asset(id, parcel_num);


--
-- PostgreSQL database dump complete
--

