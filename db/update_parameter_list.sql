update data.stations
set params= '';


update data.stations
set params = stations.params || 'current_speed,'
where station_id in (select distinct station_id from data.data_values where value1 is not null);

update data.stations
set params = stations.params || 'current_direction,'
where station_id in (select distinct station_id from data.data_values where value2 is not null);

update data.stations
set params = stations.params || 'atmospheric_pressure,'
where station_id in (select distinct station_id from data.data_values where value3 is not null);

update data.stations
set params = stations.params || 'humidity,'
where station_id in (select distinct station_id from data.data_values where value4 is not null);

update data.stations
set params = stations.params || 'rain,'
where station_id in (select distinct station_id from data.data_values where value5 is not null);

update data.stations
set params = stations.params || 'air_temp,'
where station_id in (select distinct station_id from data.data_values where value6 is not null);

update data.stations
set params = stations.params || 'wind_speed_10m_max,'
where station_id in (select distinct station_id from data.data_values where value7 is not null);

update data.stations
set params = stations.params || 'wind_speed_1_5m_max,'
where station_id in (select distinct station_id from data.data_values where value8 is not null);

update data.stations
set params = stations.params || 'wind_direction_10m,'
where station_id in (select distinct station_id from data.data_values where value9 is not null);

update data.stations
set params = stations.params || 'wind_direction_1_5m,'
where station_id in (select distinct station_id from data.data_values where value10 is not null);

update data.stations
set params = stations.params || 'wind_speed_10m_mean,'
where station_id in (select distinct station_id from data.data_values where value11 is not null);

update data.stations
set params = stations.params || 'wind_speed_1_5m_mean,'
where station_id in (select distinct station_id from data.data_values where value12 is not null);

update data.stations
set params = stations.params || 'vert_wind_speed_max,'
where station_id in (select distinct station_id from data.data_values where value13 is not null);

update data.stations
set params = stations.params || 'vert_wind_speed_mean,'
where station_id in (select distinct station_id from data.data_values where value14 is not null);

update data.stations
set params = stations.params || 'vert_wind_speed_min,'
where station_id in (select distinct station_id from data.data_values where value15 is not null);

update data.stations
set params = stations.params || 'salinity,'
where station_id in (select distinct station_id from data.data_values where value16 is not null);

update data.stations
set params = stations.params || 'sound_velocity,'
where station_id in (select distinct station_id from data.data_values where value17 is not null);

update data.stations
set params = stations.params || 'density,'
where station_id in (select distinct station_id from data.data_values where value18 is not null);

update data.stations
set params = stations.params || 'turbidity,'
where station_id in (select distinct station_id from data.data_values where value19 is not null);

update data.stations
set params = stations.params || 'water_temp,'
where station_id in (select distinct station_id from data.data_values where value20 is not null);

update data.stations
set params = stations.params || 'height,'
where station_id in (select distinct station_id from data.data_values where value21 is not null);

update data.stations
set params = stations.params || 'voltage,'
where station_id in (select distinct station_id from data.data_values where value22 is not null);

update data.stations
set params = stations.params || 'tide_height,'
where station_id in (select distinct station_id from data.data_values where value23 is not null);

update data.stations
set params = stations.params || 'wave_height,'
where station_id in (select distinct station_id from data.data_values where value24 is not null);

update data.stations
set params = stations.params || 'wave_period,'
where station_id in (select distinct station_id from data.data_values where value25 is not null);

update data.stations
set params = stations.params || 'wave_direction'
where station_id in (select distinct station_id from data.data_values where value26 is not null);
