import re
from typing import Dict, List, Tuple

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD

# --- Configurable mapping from Mermaid types to XSD ---
XSD_MAP = {
    "STRING": XSD.string,
    "INTEGER": XSD.integer,
    "INT": XSD.integer,
    "FLOAT": XSD.float,
    "DOUBLE": XSD.double,
    "BOOLEAN": XSD.boolean,
    "DATE": XSD.date,
    "DATETIME": XSD.dateTime,
}

# ---------- Parsing helpers (styling ignored) ----------

def strip_nonsemantic_lines(mermaid: str) -> str:
    """Drop comments and Mermaid styling lines."""
    out = []
    for line in mermaid.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("%%"):
            continue
        if s.startswith("classDef ") or s.startswith("class "):
            continue
        out.append(line)
    return "\n".join(out)

def parse_nodes(mermaid: str) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """
    Returns:
      node_props: { ClassName: { propName: XSD CURIE string, ... }, ... }
      classes:    [ClassName, ...]
    """
    node_props: Dict[str, Dict[str, str]] = {}
    classes: List[str] = []

    # Matches: Person["Person<br/>name: STRING | KEY<br/>year: INTEGER"]
    node_re = re.compile(r'^\s*([A-Za-z_]\w*)\s*\["(.+?)"\]\s*$', re.MULTILINE)

    for m in node_re.finditer(mermaid):
        cls = m.group(1)
        label_html = m.group(2)
        parts = [p.strip() for p in label_html.split("<br/>")]

        if cls not in node_props:
            node_props[cls] = {}
            classes.append(cls)

        for line in parts[1:]:
            if ":" not in line:
                continue
            pname, ptype = line.split(":", 1)
            pname = pname.strip()
            # ignore flags after " | "
            ptype = ptype.split("|", 1)[0].strip().upper()
            node_props[cls][pname] = ptype

    return node_props, classes

def parse_edges(mermaid: str) -> List[Tuple[str, str, str]]:
    """
    Returns list of (rel, src, tgt) for lines like: A -->|REL| B
    """
    edge_re = re.compile(
        r'^\s*([A-Za-z_]\w*)\s*-->\s*\|\s*([A-Za-z_][\w]*)\s*\|\s*([A-Za-z_]\w*)\s*$',
        re.MULTILINE,
    )
    edges = []
    for m in edge_re.finditer(mermaid):
        src, rel, tgt = m.group(1), m.group(2), m.group(3)
        edges.append((rel, src, tgt))
    return edges

# ---------- rdflib builder ----------

def mermaid_to_rdflib_graph(
    mermaid: str,
    base_uri: str = "http://example.org/ontology#",
    ontology_iri: str = "http://example.org/ontology",
) -> Graph:
    """
    Build an rdflib.Graph representing the OWL ontology derived from the Mermaid diagram.
    """
    cleaned = strip_nonsemantic_lines(mermaid)
    node_props, classes = parse_nodes(cleaned)
    edges = parse_edges(cleaned)

    g = Graph()
    NS = Namespace(base_uri)

    # Bind prefixes
    g.bind("", NS)           # default prefix
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    # Ontology header
    g.add((URIRef(ontology_iri), RDF.type, OWL.Ontology))

    # Classes
    for c in sorted(set(classes)):
        g.add((NS[c], RDF.type, OWL.Class))

    # Datatype properties
    # If multiple classes have the same property name (e.g., "name"),
    # we emit one property IRI with multiple rdfs:domain triples.
    # Range is taken from the declared XSD_MAP type (default xsd:string).
    dt_props_ranges: Dict[str, URIRef] = {}  # property -> range
    for cls, props in node_props.items():
        for pname, ptype in props.items():
            prop_iri = NS[pname]
            rng = XSD_MAP.get(ptype, XSD.string)
            # declare the property type
            g.add((prop_iri, RDF.type, OWL.DatatypeProperty))
            # domain (one triple per class using it)
            g.add((prop_iri, RDFS.domain, NS[cls]))
            # ensure consistent / at least one range triple
            # If we see conflicting declared ranges for the same property name,
            # we still add both; OWL allows multiple rdfs:range axioms (interpreted as intersection).
            g.add((prop_iri, RDFS.range, rng))

    # Object properties from edges
    for rel, src, tgt in edges:
        rel_iri = NS[rel]
        g.add((rel_iri, RDF.type, OWL.ObjectProperty))
        g.add((rel_iri, RDFS.domain, NS[src]))
        g.add((rel_iri, RDFS.range, NS[tgt]))

    return g

def mermaid_to_owl_turtle(
    mermaid: str,
    base_uri: str = "http://example.org/ontology#",
    ontology_iri: str = "http://example.org/ontology",
) -> str:
    g = mermaid_to_rdflib_graph(mermaid, base_uri, ontology_iri)
    ttl = g.serialize(format="turtle")
    # rdflib may return bytes in some versions
    return ttl.decode("utf-8") if isinstance(ttl, (bytes, bytearray)) else ttl


# ---------- Example usage ----------

if __name__ == "__main__":

    with open("ontos/blue_plaques_model.mermaid", "r", encoding="utf-8") as f:
        mermaid = f.read()
    

        ttl = mermaid_to_owl_turtle(
            mermaid,
            base_uri="http://voc.neo4j.com/blueplaques#",
            ontology_iri="http://voc.neo4j.com/blueplaques"
        )

        with open("ontos/blueplaques.ttl", "w", encoding="utf-8") as f:
            f.write(ttl)
            print(ttl)
