-- SQL scripts to create the telemetry table and some queries that are used
-- when creating the virtualized resources in neo4j with APOC

-- telemetry table creation
create table sensor_telemetry(
  datetime TIMESTAMPTZ,
  device_id int,
  metric varchar(100),
  reading bigint
  );

-- 100 records and record count SQL queries
SELECT datetime, device_id, metric, reading
FROM public.sensor_telemetry
LIMIT 100 ;

SELECT count(*)
FROM public.sensor_telemetry;


-- last 30 second readings for a given device and metric
select * from sensor_telemetry st
where st.device_id = 2 and st.metric = 'M-3' and st.datetime > now() - INTERVAL '30 seconds';

-- aggregates (count, avg, max/min) by metric over the last 30 seconds
-- for a given device
select metric, count(*) as reading_count, avg(reading) as avg_reading , min(reading) as min_reading,
max(reading) as max_reading, min(datetime) as from_time, max(datetime) as to_time
from sensor_telemetry st
where st.device_id = 4 and st.datetime > now() - INTERVAL '30 seconds' group by device_id , metric ; 
