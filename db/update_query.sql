update data.stations
set string_name_id = station_name ||'-'|| deployment_id ||'-' || locationid;


drop view data.station_date_temp_start;
create view data.station_date_temp_start as (select distinct station_id,min(collection_date) from data.data_values group by station_id);

update data.stations
set start_date = (select min from data.station_date_temp_start where data.stations.station_id = data.station_date_temp_start.station_id);


drop view data.station_date_temp_end;
create view data.station_date_temp_end as (select distinct station_id,max(collection_date) from data.data_values group by station_id);

update data.stations
set end_date = (select max from data.station_date_temp_end where data.stations.station_id = data.station_date_temp_end.station_id);


update data.stations
set station_geom = ST_SetSRID(ST_MakePoint(lon_loc,lat_loc),4326);


update data.stations
set depth_var = (select string_agg(depth::char(4), ',') from data.depth_lookup_profile where depth_lookup_profile.station_id = stations.station_id);



#to round date to nearest 10 mintues
CREATE OR REPLACE FUNCTION round_time10(TIMESTAMP WITH TIME ZONE) 
RETURNS TIMESTAMP WITH TIME ZONE AS $$ 
  SELECT date_trunc('hour', $1) + INTERVAL '10 min' * ROUND(date_part('minute', $1) / 10.0) 
$$ LANGUAGE SQL;

update data.data_values
set collection_date = round_time10(collectiondate);

select round_time10(to_timestamp('2012-02-13 01:42:38', 'YYYY-MM-DD HH:MI:SS'));


#attempt to stride data
create table data.data_values_1h as (
select distinct on(collection_date2,station_id,sensor_id,depth) date_trunc('hour', collection_date) as collection_date, station_id, value1, sensor_id, depth, value2, value3, value4, 
value5, value6, value7, value8, value9, value10, value11, value12, value13, value14, value15, value16, value17, value18, value19, value20, value21, 
value22, value23, value24, value25, value26 from data.data_values)


CREATE INDEX index_list_station_id_1h
  ON data.data_values_1h
  USING btree
  (station_id );

  CREATE INDEX index_list_sensor_id_1h
  ON data.data_values_1h
  USING btree
  (sensor_id );


CREATE INDEX depth_roundfull_idx_1h
  ON data.data_values_1h
  USING btree
  (depth );


CREATE INDEX date_indexfull_idx_1h
  ON data.data_values_1h
  USING btree
  (collection_date );
ALTER TABLE data.data_values_1h CLUSTER ON date_indexfull_idx_1h;