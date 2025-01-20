from rdflib import URIRef, Graph
from rdflib.namespace import RDF, RDFS, OWL, XSD
from collections import defaultdict
import requests
from DIMNodeDef import DIMNodeDef
import json
import math
import os

class DIModelBuilder:
    MAX_NUM_NODES = 25
    MAX_NUM_RELS = 250

    def __init__(self):
        self.model_def = {}
        self.g = Graph()

    def build_di_model(self, rdf_data, rdf_format, props):
        uri_map = defaultdict(set)
        class_list = props.get("classList", [])

        urilist = self._format_uri_list(class_list) if class_list else None

        
        self.g.parse(data=rdf_data, format=rdf_format)
        
        # Build initial class hierarchy
        all_classes = set()
        
        catsQuery = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            select distinct ?explicit ?parent 
            where {{ 
                ?explicit rdfs:subClassOf* ?parent 
                filter( ?explicit in ( {urilist} ) && isIRI(?parent)) 
              }} """
        
        allCatsQuery = """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            select distinct ?explicit ?parent
            where {
              ?explicit a ?classtype    
                filter( (?classtype in ( owl:Class, rdfs:Class )) && not exists { ?x rdfs:subClassOf ?explicit })               
              ?explicit rdfs:subClassOf* ?parent
                filter( isIRI(?parent) )
              }"""
        
        for row in self.g.query(catsQuery if not class_list==[] else allCatsQuery):
            parent = row.parent
            all_classes.add(parent)            
            uri_map[parent].add(row.explicit)

        explicit_class_set = set()  
        for key, vals in uri_map.items():            
            for v in vals:
                explicit_class_set.add(v)

        if len(explicit_class_set) > self.MAX_NUM_NODES:
            raise RuntimeError(f"The ontology contains too many classes ({len(explicit_class_set)}). Please limit the 'classList'.")

        for cls in explicit_class_set:
            self.model_def[cls] = DIMNodeDef(cls)

        urilist = self._format_uri_list(all_classes)

        propsQuery = f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sch: <https://schema.org/>
            select distinct ?prop ?domain ?range
            where {{
              ?prop a ?propertyClass .
              filter(?propertyClass in (rdf:Property, owl:DatatypeProperty, owl:FunctionalProperty ))
              {{
                ?prop ?domainPred ?domain
                filter(?domainPred in (sch:domainIncludes, rdfs:domain) &&
                ?domain in ( {urilist} ))
              }} union {{
                ?prop ?domainPred [ owl:unionOf/rdf:rest*/rdf:first  ?domain ]
                filter(?domainPred in (sch:domainIncludes, rdfs:domain) &&
                ?domain in ( {urilist} ))
              }}
              optional {{
                ?prop ?rangePred ?range
                filter(?rangePred in (sch:rangeIncludes, rdfs:range) && 
                (?range in ( sch:Text ) || regex(str(?range),\"^http://www.w3.org/2001/XMLSchema#.*\")))
              }}
            }}"""
        
        relsQuery = f"""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            prefix sch: <https://schema.org/>
            select distinct ?prop ?domain ?range
            where {{
            
               filter(?domain in ( {urilist} )
                && ?range in ( {urilist} ))
              
              ?prop a ?propertyClass .
              filter(?propertyClass in (rdf:Property, owl:ObjectProperty, owl:FunctionalProperty, owl:AsymmetricProperty, 
             owl:InverseFunctionalProperty, owl:IrreflexiveProperty, owl:ReflexiveProperty, owl:SymmetricProperty, owl:TransitiveProperty))
            
              {{
                ?prop ?domainPred ?domain ; ?rangePred ?range .
                filter(?domainPred in (sch:domainIncludes, rdfs:domain) && ?rangePred in (sch:rangeIncludes, rdfs:range))
              }} union {{
                ?prop ?domainPred [ owl:unionOf/rdf:rest*/rdf:first  ?domain ]
                      filter(?domainPred in (sch:domainIncludes, rdfs:domain) )
              }} union {{
                ?domain rdfs:subClassOf [ a                   owl:Restriction ;
                                        owl:onProperty      ?prop ;
                                        ?restrictionPred  ?range
                                     ] ;
                      filter(?restrictionPred in (owl:someValuesFrom, owl:allValuesFrom ))
              }} union {{
                ?domain rdfs:subClassOf [ a                   owl:Restriction ;
                                        owl:onProperty      ?prop ;
                                        ?cardinalityRestriction  ?card ;
                                        owl:onClass ?range 
                                      ] ;
                      filter(?cardinalityRestriction in (owl:qualifiedCardinality, owl:minQualifiedCardinality, 
              owl:maxQualifiedCardinality ))
              }}
            
            }}"""

        # Relationships
        self._add_rels(self.g, uri_map, relsQuery)

        # Properties
        self._add_props(self.g, uri_map, propsQuery)

    def _format_uri_list(self, urilist):
        return ", ".join(f"<{uri}>" for uri in urilist)

    def _add_props(self, graph, uri_map, query):
        for record in graph.query(query):
            for domain in uri_map[record.domain]:
                self.model_def[domain].add_prop(record.prop, record.range or XSD.string)

    def _add_rels(self, graph, uri_map, query):
        for record in graph.query(query):
            domain = record.domain
            range_ = record.range
            if domain in uri_map and range_ in uri_map:
                for d in uri_map[domain]:
                    for r in uri_map[range_]:
                        self.model_def[d].add_rel(record.prop, r)

    def assign_positions_to_nodes(self):
        rows = math.ceil(math.sqrt(len(self.model_def) / 2))
        cols = 2 * rows
        step_h = 1200 // cols
        step_v = 600 // rows
        x_start, y_start = -1000 + step_h // 2, step_v // 2

        for i, node in enumerate(self.model_def.values()):
            x = x_start + ((i % cols) * step_h)
            y = y_start + ((i // cols) * step_v)
            node.set_pos(x, y)

    def get_model_as_serialisable_object_v01(self):
        self.assign_positions_to_nodes()

        nodes = [node.get_graph_node_as_json() for node in self.model_def.values()]
        
        relationships = [
            rel for node in self.model_def.values() for rel in node.get_graph_rels_as_json()
        ]

        relMappings = {} 
        relSchemas = {}
        for k, v in self.model_def.items():
            relMappings.update(v.get_rels_mappings_as_json()) 
            relSchemas.update(v.get_rel_schemas_as_json())
            
        data_model = {
            "fileModel": {"fileSchemas": {}},
            "graphModel": {
                "nodeSchemas": {str(k): v.get_node_schemas_as_json() for k, v in self.model_def.items()},
                "relationshipSchemas": relSchemas,
            },
            "mappingModel": {
                "nodeMappings": {str(k): v.get_node_mappings_as_json() for k, v in self.model_def.items()},
                "relationshipMappings": relMappings,
            },
        }

        return {
            "version": "0.1.1-beta.0",
            "graph": {"nodes": nodes, "relationships": relationships},
            "dataModel": data_model,
        }
    
    def get_model_as_serialisable_object_v2(self, use_labels=False, make_schema_query_friendly=False):
        self.assign_positions_to_nodes()

        nodes = []
        node_object_types = []
        node_pos = 0
        for node in self.model_def.values():
            nodes.append(node.get_graph_node_as_json_v2(node_pos))
            node_object_types.append(node.get_node_object_type_v2(node_pos))
            node_pos+=1
    
        node_schemas = []
        rel_schemas = []

        for k, v in self.model_def.items():
            node_schemas.append(v.get_node_schemas_as_json_v2(self.g, use_labels, make_schema_query_friendly)) 
            rel_schemas.extend(v.get_rel_schemas_v2(self.g, use_labels, make_schema_query_friendly))

        rel_object_types = []
        pos = 0
        for node in self.model_def.values():
            rel_object_types.extend(node.get_rel_object_type_v2(pos, node_object_types))
            pos=len(rel_object_types)

        return {
            "version": "2.2.0",
            "visualisation" : { "nodes" : nodes },
            "dataModel" : {
                "version": "2.2.0",
                "graphSchemaRepresentation": {
                    "version": "1.0.0",
                    "graphSchema": {
                        "nodeLabels": node_schemas,
                        "relationshipTypes": rel_schemas,
                        "nodeObjectTypes": node_object_types,
                        "relationshipObjectTypes": rel_object_types,
                        "constraints": [],
                        "indexes": []
                    }
                },
                "graphSchemaExtensionsRepresentation": {
                "nodeKeyProperties": []
                },
                "graphMappingRepresentation": {
                "dataSourceSchema": {
                    "type": None,
                    "tableSchemas": []
                },
                "nodeMappings": [],
                "relationshipMappings": []
                },
                "configurations": {
                "idsToIgnore": []
                }
            }
        }

    def export_model_to_file(self, output_path, model):
        with open(output_path, "w") as f:
            json.dump(model, f, indent=2)
        print(f"Model exported to {output_path}")






if __name__ == "__main__":
    link = "http://localhost:8000/ontos/sales-onto.ttl"
    # "http://localhost:8000/ontos/insurance.ttl"
    # "https://raw.githubusercontent.com/datadotworld/cwd-benchmark-data/refs/heads/main/ACME_Insurance/ontology/insurance.ttl"
    # "https://bimerr.iot.linkeddata.es/def/building/ontology.ttl"
    
    resp = requests.get(link)
    theonto = resp.text
    #print(theonto)
    
    use_labels = False 
    make_schema_query_friendly = False

    mb = DIModelBuilder()
    mb.build_di_model(theonto, "ttl", {})
    #   If we want to filter the list of classes to use
    #   {"classList": ["http://bimerr.iot.linkeddata.es/def/building#Building",
    #                                  "http://bimerr.iot.linkeddata.es/def/building#Space",
    #                                  "http://bimerr.iot.linkeddata.es/def/building#Element"]})
    for k,v in mb.model_def.items():
        print(k)
        print(v.summary(mb.g, use_labels, make_schema_query_friendly))
    
    mb.export_model_to_file("output_new.json", mb.get_model_as_serialisable_object_v2(use_labels, make_schema_query_friendly))

