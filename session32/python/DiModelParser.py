import json, re
from rdflib import URIRef, Literal, Graph
from rdflib.namespace import RDF, RDFS, OWL, XSD

class JSONGraphParser:
    
    model = {}
    default_base_ns = "http://voc.neo4j.com/"

    def __init__(self, file_path):
        with open(file_path, 'r') as file:
            self.data = json.load(file)

    def parse_nodes(self):
        node_object_types = {}
        for x in self.data["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["nodeObjectTypes"] :
            node_object_types[x["$id"]] = x["labels"][0]["$ref"][1:] 
        nodes = self.data["visualisation"]["nodes"]
        parsed_nodes = []
        for node in nodes:
            parsed_nodes.append({
                "id": node["id"],
                "position": node["position"],
                "first_label" : node_object_types[node["id"]]
            })
        return parsed_nodes

    def parse_node_labels(self):
        labels = self.data["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["nodeLabels"]
        parsed_labels = {}
        for label in labels:
            properties = [{
                "id": prop["$id"],
                "token": prop["token"],
                "type": prop["type"]["type"],
                "nullable": prop.get("nullable", False)
            } for prop in label["properties"]]
            parsed_labels[label["$id"]] = {
                "token": label["token"],
                "properties": properties
            }
        return parsed_labels
    
    def parse_rel_types(self):
        rel_types = self.data["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["relationshipTypes"]
        parsed_rel_types = {}
        for rt in rel_types:
            properties = [{
                "id": prop["$id"],
                "token": prop["token"],
                "type": prop["type"]["type"],
                "nullable": prop.get("nullable", False)
            } for prop in rt["properties"]]
            parsed_rel_types[rt["$id"]] = {
                "token": rt["token"],
                "properties": properties
            }
        return parsed_rel_types

    def parse_relationships(self):
        relationships = self.data["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["relationshipObjectTypes"]
        parsed_relationships = []
        for relationship in relationships:
            parsed_relationships.append({
                "id": relationship["$id"],
                "type": relationship["type"]["$ref"][1:],
                "from": relationship["from"]["$ref"][1:],
                "to": relationship["to"]["$ref"][1:]
            })
        return parsed_relationships

    def parse_constraints(self):
        constraints = self.data["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["constraints"]
        parsed_constraints = []
        for constraint in constraints:
            parsed_constraints.append({
                "id": constraint["$id"],
                "name": constraint["name"],
                "type": constraint["constraintType"],
                "entity": constraint["entityType"],
                "node_label": constraint["nodeLabel"]["$ref"],
                "properties": [prop["$ref"] for prop in constraint["properties"]]
            })
        return parsed_constraints

    def parse_indexes(self):
        indexes = self.data["dataModel"]["graphSchemaRepresentation"]["graphSchema"]["indexes"]
        parsed_indexes = []
        for index in indexes:
            parsed_indexes.append({
                "id": index["$id"],
                "name": index["name"],
                "type": index["indexType"],
                "entity": index["entityType"],
                "node_label": index["nodeLabel"]["$ref"],
                "properties": [prop["$ref"] for prop in index["properties"]]
            })
        return parsed_indexes

    def parse(self):
        self.model =  {
            "nodes": self.parse_nodes(),
            "node_labels": self.parse_node_labels(),
            "relationships": self.parse_relationships(),
            "rel_types": self.parse_rel_types(),
            # "constraints": self.parse_constraints(),
            # "indexes": self.parse_indexes()
        }
    
    def serialise_as_owl(self):        

        onto = Graph()
        for k,v in self.model["node_labels"].items():
            onto.add((self.get_URI(k),RDF.type,OWL.Class))
            onto.add((self.get_URI(k),RDFS.label,Literal(v["token"])))
            for prop in v["properties"]:
                if not prop["token"] in ["uri", "label", "comment"]:
                    onto.add((self.get_URI(prop["id"]),RDF.type,OWL.DatatypeProperty))
                    onto.add((self.get_URI(prop["id"]),RDFS.domain,self.get_URI(k)))
                    onto.add((self.get_URI(prop["id"]),RDFS.label,Literal(prop["token"])))
                    onto.add((self.get_URI(prop["id"]),RDFS.range,self.convert_to_di_data_type(prop["type"])))
        for rel in self.model["relationships"]:
            onto.add((self.extract_rel_uri(rel["type"]),RDF.type,OWL.ObjectProperty))
            onto.add((self.extract_rel_uri(rel["type"]),RDFS.domain,self.translate_ref(rel["from"])))
            onto.add((self.extract_rel_uri(rel["type"]),RDFS.range,self.translate_ref(rel["to"])))
            onto.add((self.extract_rel_uri(rel["type"]),RDFS.label,self.get_rel_label(rel["type"])))       
        return onto.serialize()

    def translate_ref(self, node_ref):
        result = OWL.Thing
        for x in self.model["nodes"]:
            if x["id"] == node_ref:
                result = self.get_URI(x["first_label"])
        return result 
    
    def get_rel_label(self, rel_id):
        if rel_id in self.model["rel_types"].keys():
            return Literal(self.model["rel_types"][rel_id]["token"] or "")
    
    def get_URI(self,id):
        uri = id
        mo = re.match(r"(p|rt|nl):(\d+)",id)
        if mo:
            #it's a numeric id generated by the modeller
            if mo.group(1) == "rt":
                uri = self.default_base_ns + "rel_" + mo.group(2)
            if mo.group(1) == "nl":
                uri = self.default_base_ns + "cat_" + mo.group(2)
            if mo.group(1) == "p":
                uri = self.default_base_ns + "prop_" + mo.group(2)
            else:
                uri = self.default_base_ns + mo.group(1) + "_" + mo.group(2)
        return URIRef(uri)
        
    def extract_rel_uri(self, raw_uri):
        sub_uris = raw_uri.split("http")
        if len(sub_uris) == 4:
            return URIRef("http" + sub_uris[2])
        elif raw_uri.startswith("http"):
            return URIRef(raw_uri)
        else:
            return self.get_URI(raw_uri)

    @staticmethod
    def convert_to_di_data_type(datatype):
        if datatype == "integer":
            return XSD.integer
        elif datatype == "float": 
            return XSD.decimal
        elif datatype == "boolean": 
            return XSD.boolean
        elif datatype == "datetime": 
            return XSD.dateTime
        else:
            return XSD.string

if __name__ == "__main__":
    file_path = "di-native.json"
    parser = JSONGraphParser(file_path)
    parser.parse()
    print(parser.serialise_as_owl())
    
