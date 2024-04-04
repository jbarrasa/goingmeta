// We select a few classes from the onto and we generate a config file that we can then use in the import tool in Neo4j's workspace
// the export.dimodel procedure will save the config file on your local drive

call n10s.experimental.export.dimodel.fetch("https://raw.githubusercontent.com/datadotworld/cwd-benchmark-data/main/ACME_Insurance/ontology/insurance.ttl",
                                            "Turtle", {classList: ["http://data.world/schema/insurance/Policy",
                                                                   "http://data.world/schema/insurance/PolicyHolder",
                                                                   "http://data.world/schema/insurance/Agent"]});


// Alternatively, the stream.dimodel procedure will return it as query result on your browser 

call n10s.experimental.stream.dimodel.fetch("https://raw.githubusercontent.com/datadotworld/cwd-benchmark-data/main/ACME_Insurance/ontology/insurance.ttl",
                                            "Turtle", {classList: ["http://data.world/schema/insurance/Policy",
                                                                   "http://data.world/schema/insurance/PolicyHolder",
                                                                   "http://data.world/schema/insurance/Agent"]})

// The config file generated is in the 'assets' folder in this repo

// You can now use it in the Neo4j import tool as seen in the webcast and explore the model and map it to the source files

// The source CSV files can be downloaded from the data.world github repo 
// https://github.com/datadotworld/cwd-benchmark-data/tree/main/ACME_Insurance/data

// When you're done with the mapping, you can run the import job to populate the Neo4j Graph DB

// We can query the graph in Neo4j now, for example if we want to get the aggregate
// number of policies sold by each agent, we can use this simple ypher 

MATCH (p:Policy)-[:soldByAgent]->(a:Agent) 
RETURN a.agentId AS AgentID, COUNT(p) AS PoliciesSold

// Check out the RAG part of the sesion in the python notebook in this repo where we:
// * Prompt the LLM with a natural language question from the data.world benchmark 
// * and pass as context the graph schema that we can dynamically retrieve with the query below
// The expectation is that the LLM will be able to generate the correct cypher


// A graph in Neo4j is self describing and we can introspect it to get all the schema details:

// All node types and their properties 
call db.schema.nodeTypeProperties()

// And same with the relationships
call apoc.meta.relTypeProperties()
