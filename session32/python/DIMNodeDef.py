from rdflib import URIRef, RDFS, XSD
from collections import defaultdict
import json


class DIMNodeDef:
    def __init__(self, node_id):
        self.node_id = URIRef(node_id)
        self.props = {
            # RDFS.label: XSD.string,
            # RDFS.comment: XSD.string,
            # URIRef("neo4j://graph.schema#uri"): XSD.string
        }
        self.rels = defaultdict(set)
        self.x = 0
        self.y = 0

    def summary(self, g, use_labels = False, make_schema_query_friendly = False):
        return f"\nID: {self._get_label_if_available_or_local(self.node_id, g, use_labels, make_schema_query_friendly)} \n - PROPS:  \n{self.map_as_string(self.props, g, use_labels, make_schema_query_friendly)}\n - RELS:  \n{self.map_of_sets_as_string(self.rels, g, use_labels, make_schema_query_friendly)}\n"
  
    def map_as_string(self, m, g, use_labels, make_schema_query_friendly):
        return "  \n".join([f"\t{self._get_label_if_available_or_local(key, g, use_labels, make_schema_query_friendly)}: {getLocalPart(value) if value else ' - '}" for key, value in m.items()])

    def map_of_sets_as_string(self,m, g, use_labels, make_schema_query_friendly):
        return "  \n".join(
            [f"\t{self._get_label_if_available_or_local(key, g, use_labels, make_schema_query_friendly)}: " + " ".join([self._get_label_if_available_or_local(rel, g, use_labels, make_schema_query_friendly) for rel in rels]) for key, rels in m.items()]
        )

    def get_node_schemas_as_json(self):
        properties = [
            {"property": str(getLocalPart(key)), 
             "type": self.convert_to_di_data_type(value),
             "identifier": str(key)}
            for key, value in self.props.items()
        ]
        return {
            "label": getLocalPart(self.node_id),
            "additionLabels": [],
            "labelProperties": [],
            "properties": properties,
            "key": {"properties": [], "name": ""}
        }
    
    def get_node_schemas_as_json_v2(self, graph, use_labels, make_schema_query_friendly):
        p_count = 0
        properties = [
            {
                "$id":  str(key),
                "token": self._get_label_if_available_or_local(key, graph, use_labels, make_schema_query_friendly), 
                "type": { "type": self.convert_to_di_data_type(value)},
                "nullable": True }
            for key, value in self.props.items()
        ]        
        return {
            "$id": str(self.node_id) , 
            "token": self._get_label_if_available_or_local(self.node_id, graph, use_labels, make_schema_query_friendly),
            "properties": properties
        }
    
    @staticmethod
    def _get_label_if_available_or_local(uri, graph, use_labels, make_schema_query_friendly):
                
        labelsQuery = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            select distinct ?label
            where {{            
               {"<" + str(uri) + ">"} rdfs:label ?label .
               filter(isLiteral(?label) && (lang(?label)='en' || lang(?label) = ''))
            }}"""

        result = getLocalPart(uri)

        if use_labels:
            # not dealing properly with multi-lingual or multi-labelled ontos 
            for record in graph.query(labelsQuery):
                result = record.label

            if make_schema_query_friendly:
                # whatever we want to do. Maybe camel case? for now only underscore spaces
                result = result.replace(" ","_")    
            
        return str(result)

    @staticmethod
    def convert_to_di_data_type(datatype):
        if datatype in {XSD.integer, XSD.int, XSD.positiveInteger, XSD.negativeInteger, XSD.nonPositiveInteger,
                        XSD.nonNegativeInteger, XSD.long, XSD.short, XSD.unsignedLong, XSD.unsignedShort}:
            return "integer"
        elif datatype in {XSD.decimal, XSD.float, XSD.double}:
            return "float"
        elif datatype == XSD.boolean:
            return "boolean"
        else:
            return "string"

    def get_rel_schemas_as_json(self):
        return {
            f"{self.node_id}{rel}{target}": {
                "type": getLocalPart(rel),
                "sourceNodeSchema": str(self.node_id),
                "targetNodeSchema": str(target),
                "properties": []
            }
            for rel, targets in self.rels.items()
            for target in targets
        }
    
    def get_rel_schemas_v2(self, graph, use_labels, make_schema_query_friendly):
        return [{
                "$id" : f"{self.node_id}{rel}{target}",
                "token": self._get_label_if_available_or_local(rel, graph, use_labels, make_schema_query_friendly),
                "properties": []
                } for rel, targets in self.rels.items() for target in targets]

    def get_node_mappings_as_json(self):
        return {
            "nodeSchema": str(self.node_id),
            "mappings": []
        }

    def get_rels_mappings_as_json(self):
        return {
            f"{self.node_id}{rel}{target}": {
                "relationshipSchema": f"{self.node_id}{rel}{target}",
                "mappings": [],
                "sourceMappings": [],
                "targetMappings": []
            }
            for rel, targets in self.rels.items()
            for target in targets
        }

    def get_graph_node_as_json(self):
        return {
            "id": str(self.node_id),
            "position": {"x": self.x, "y": self.y},
            "caption": getLocalPart(self.node_id)
        }
    
    def get_graph_node_as_json_v2(self, pos):
        return {
            "id": str("n:" + str(pos)),
            "position": {"x": self.x, "y": self.y}
        }
    
    def get_node_object_type_v2(self, pos):
        return {
            "$id": str("n:" + str(pos)),
            "labels": [{ "$ref": "#" + str(self.node_id) }] 
        }

    def get_graph_rels_as_json(self):
        return [
            {
                "id": f"{self.node_id}{rel}{target}",
                "type": getLocalPart(rel),
                "fromId": str(self.node_id),
                "toId": str(target)
            }
            for rel, targets in self.rels.items()
            for target in targets
        ]
    
    def get_rel_object_type_v2(self, pos, node_object_types):
        result = []
        for rel, targets in self.rels.items():
            for target in targets:
                result.append({
                        "$id": "r:" + str(pos), 
                        "type": { "$ref": f"#{self.node_id}{rel}{target}" },
                        "from": { "$ref": self.get_node_id(self.node_id, node_object_types)},
                        "to": { "$ref": self.get_node_id(target, node_object_types)}
                    })
                pos+=1
        return result
    
    @staticmethod
    def get_node_id(node_type_id, node_object_types):
        for nt in node_object_types:
            if str(node_type_id) == [ x["$ref"][1:] for x in nt["labels"]][0]:
                return "#" + nt["$id"] 

    def add_prop(self, prop, datatype):
        self.props[URIRef(prop)] = URIRef(datatype)

    def add_rel(self, rel, range_):
        self.rels[URIRef(rel)].add(URIRef(range_))

    def set_pos(self, x, y):
        self.x = x
        self.y = y

    def get_rel_count(self):
        return sum(len(targets) for targets in self.rels.values())
    
    #utility function to get the local part of a URI (stripping out the namespace)


def getLocalPart(uri):
    pos = -1
    pos = uri.rfind('#') 
    if pos < 0 :
        pos = uri.rfind('/')  
    if pos < 0 :
        pos = uri.rindex(':')
    return uri[pos+1:]

def getNamespacePart(uri):
    pos = -1
    pos = uri.rfind('#') 
    if pos < 0 :
        pos = uri.rfind('/')  
    if pos < 0 :
        pos = uri.rindex(':')
    return uri[0:pos+1]
