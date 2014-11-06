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


select round_time10(to_timestamp('2012-02-13 01:42:38', 'YYYY-MM-DD HH:MI:SS'));


