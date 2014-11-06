update data.stations
set pretty_params= '';


update data.stations
set pretty_params = stations.pretty_params || 'Current Speed,'
where station_id in (select distinct station_id from data.data_values where value1 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Current Direction,'
where station_id in (select distinct station_id from data.data_values where value2 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean Atmospheric Pressure,'
where station_id in (select distinct station_id from data.data_values where value3 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean Humidity,'
where station_id in (select distinct station_id from data.data_values where value4 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Rain Amount,'
where station_id in (select distinct station_id from data.data_values where value5 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean Air Temperature,'
where station_id in (select distinct station_id from data.data_values where value6 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Max 10m Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value7 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Max 1.5m Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value8 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean 10m Wind Direction,'
where station_id in (select distinct station_id from data.data_values where value9 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean 1.5m Wind Direction,'
where station_id in (select distinct station_id from data.data_values where value10 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean 10m Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value11 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean 1.5m Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value12 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Max Vertical Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value13 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean Vertical Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value14 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Min Vertical Wind Speed,'
where station_id in (select distinct station_id from data.data_values where value15 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Salinity,'
where station_id in (select distinct station_id from data.data_values where value16 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Sound Velocity,'
where station_id in (select distinct station_id from data.data_values where value17 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Density,'
where station_id in (select distinct station_id from data.data_values where value18 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Turbidity,'
where station_id in (select distinct station_id from data.data_values where value19 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Mean Water Temperature,'
where station_id in (select distinct station_id from data.data_values where value20 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Water Height,'
where station_id in (select distinct station_id from data.data_values where value21 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Voltage from Tide,'
where station_id in (select distinct station_id from data.data_values where value22 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Tide Height,'
where station_id in (select distinct station_id from data.data_values where value23 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Water Surface Elevation,'
where station_id in (select distinct station_id from data.data_values where value24 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Wave Period,'
where station_id in (select distinct station_id from data.data_values where value25 is not null);

update data.stations
set pretty_params = stations.pretty_params || 'Wave Direction'
where station_id in (select distinct station_id from data.data_values where value26 is not null);
