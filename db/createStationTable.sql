-- Table: data.stations

-- DROP TABLE data.stations;

CREATE TABLE data.stations
(
  station_id serial NOT NULL,
  station_name character varying(15),
  alt_name character varying(50),
  station_desc character varying(500),
  location_type character varying(50) DEFAULT 'absolute'::character varying,
  lat_loc numeric,
  lon_loc numeric,
  client_id integer NOT NULL DEFAULT 1,
  station_geom geometry(Point,4326),
  deployment_id integer,
  string_name_id character varying(20),
  notes character varying(200),
  issues character varying(200),
  locationid integer DEFAULT 1,
  start_date timestamp without time zone,
  end_date timestamp without time zone,
  CONSTRAINT pk_station PRIMARY KEY (station_id )
)
WITH (
  OIDS=FALSE
);
ALTER TABLE data.stations
  OWNER TO postgres;

-- Index: data.station_id_idx1

-- DROP INDEX data.station_id_idx1;

CREATE INDEX station_id_idx1
  ON data.stations
  USING btree
  (station_id );

