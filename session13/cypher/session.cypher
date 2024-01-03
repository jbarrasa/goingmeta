// STEP 1:
// Populate the db with the network topology dataset (in data folder)

// Create devices
load csv with headers from "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session13/data/devices.csv" as row
create (d:Device) set d = row

// add references to link with telemetry data in time series DB
MATCH (d:Device) set d.external_id = tointeger(substring(d.neId,1))

// Create links
load csv with headers from "https://raw.githubusercontent.com/jbarrasa/goingmeta/main/session13/data/links.csv" as row
match (from:Device { neId : row.from })
match (to:Device { neId : row.to })
merge (from)-[l:link]->(to) set l.capacity = row.capacity, l.linkId = row.linkId


// STEP 1.5 (Optional):
// You can create a map view in Neodash using this simple query to explore a
// geolocated view of the topology
match (d1:Device)-[r:link]->(d2)
return d1, r, d2


// STEP 2:
// Create the virtualized resources using `apoc.dv.catalog.add` and query them
// using `apoc.dv.query` and `apoc.dv.queryAndLink`

CALL apoc.dv.catalog.add("all-metrics-10s", {
  type: "JDBC",
  url: "jdbc:postgresql://localhost/jb?user=jb&password=jb",
  labels: ["RawMetric"],
  query: "select * from sensor_telemetry st
          where st.device_id = $deviceid
          and datetime > now() - INTERVAL '10 seconds';",
  desc: "last 10 seconds of all metrics by device Id"
})


CALL apoc.dv.catalog.add("named-metric-10s", {
  type: "JDBC",
  url: "jdbc:postgresql://localhost/jb?user=jb&password=jb",
  labels: ["RawMetric"],
  query: "select * from sensor_telemetry st
          where st.device_id = $deviceid and st.metric = $metricname
          and st.datetime > now() - INTERVAL '10 seconds';",
  desc: "last 10 seconds of a specific metric by device Id"
})


// Retrieve the raw metrics from the time series db and aggregate them in
// neo4j with cypher producing a result that combines data from the graph database
// and from the external time series DB.
match (d:Device {name: "Versailles"})
call apoc.dv.query("all-metrics-10s", { deviceid: d.external_id }) yield node as reading
with d, apoc.any.properties(reading) as reading
return d.neId as deviceId, d.code as deviceCode, d.lat as latitude, d.long as longitude,
       reading.metric as metric, avg(reading.reading) as avg_value,
       min(reading.reading) as min_value, max(reading.reading) as max_value,
       min(reading.datetime) as from, max(reading.datetime) as to limit 100

// Retrieve a raw metric (M-5) for a given device and link the nodes virtually
MATCH (d:Device) where d.name = "Orly Nord"
CALL apoc.dv.queryAndLink(d,"has_metric",
       "named-metric-10s", { deviceid: d.external_id , metricname: "M-5"}) YIELD path
RETURN *

// virtualized resource returning aggregates for all metrics over the last 10 seconds
CALL apoc.dv.catalog.add("agg-metrics-30s", {
  type: "JDBC",
  url: "jdbc:postgresql://localhost/jb?user=jb&password=jb",
  labels: ["AggregateMetric"],
  query: "select metric, count(*) as reading_count, avg(reading) as avg_reading ,
          min(reading) as min_reading, max(reading) as max_reading,
          min(datetime) as from_time, max(datetime) as to_time
          from sensor_telemetry st
          where st.device_id = $deviceid and st.datetime > now() - INTERVAL '30 seconds'
          group by device_id , metric ; ",
  desc: "last 10 seconds of aggregated metrics by device Id"
})

// Iterate over all devices in the topology and retrieve the aggregates for
// all metrics over the last 10 seconds
// the query returns a graph combining the topology info from the graph database
// and the telemetry info retrieved and aggregated on demand from the time
// series database
// note how we aggregate the links in line 1 to avoid generating multiple
// redundant requests to the time series database
match (d:Device)-[l:link]-() with d, collect(l) as links
call apoc.dv.queryAndLink(d,"has_aggregate_metric",
                  "agg-metrics-30s", { deviceid: d.external_id }) yield path
return *


// STEP 3:
// Serialize the results of the previous queries as RDF using the HTTP/RDF cypher
// endpoint in Neosemantics
// Note we use only single quotes in the cypher query as it is inside double
// quotes in the JSON payload of the POST request

:post http://localhost:7474/rdf/neo4j/cypher
{"cypher" : "MATCH (d:Device) where d.name = 'Orly Nord' CALL apoc.dv.queryAndLink(d,'has_metric','named-metric-10s', { deviceid: d.external_id , metricname: 'M-5'}) YIELD path RETURN *"}
