#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD

# ---------- Configurable: XSD → Mermaid type mapping ----------
XSD_TO_MERMAID = {
    XSD.string: "STRING",
    XSD.integer: "INTEGER",
    XSD.int: "INTEGER",
    XSD.long: "INTEGER",
    XSD.short: "INTEGER",
    XSD.byte: "INTEGER",
    XSD.unsignedInt: "INTEGER",
    XSD.unsignedLong: "INTEGER",
    XSD.unsignedShort: "INTEGER",
    XSD.unsignedByte: "INTEGER",
    XSD.decimal: "DOUBLE",
    XSD.float: "FLOAT",
    XSD.double: "DOUBLE",
    XSD.boolean: "BOOLEAN",
    XSD.date: "DATE",
    XSD.dateTime: "DATETIME",
    XSD.time: "STRING",
    XSD.anyURI: "STRING",
    XSD.language: "STRING",
}

DEFAULT_MERMAID_TYPE = "STRING"

# ---------- Helpers ----------

def local_name(term: URIRef, fallback_prefix: str = "C") -> str:
    """
    Get a readable local name from a URIRef. Falls back to a safe identifier.
    """
    if not isinstance(term, URIRef):
        return str(term)

    s = str(term)
    if "#" in s:
        cand = s.rsplit("#", 1)[1]
    else:
        cand = s.rsplit("/", 1)[-1]

    if not cand:
        cand = s

    # Make it a valid Mermaid identifier (letters, digits, underscore)
    cand = re.sub(r"[^A-Za-z0-9_]", "_", cand)
    if not re.match(r"^[A-Za-z_]", cand):
        cand = f"{fallback_prefix}_{cand}"
    return cand

def first_mermaid_type(ranges: Iterable[URIRef]) -> str:
    """
    Choose a display type name for a set of XSD ranges.
    If multiple ranges exist, pick a consistent representative (prefers more specific).
    """
    # prioritize by an ordered list
    priority = [
        XSD.integer, XSD.int, XSD.long, XSD.short, XSD.byte,
        XSD.float, XSD.double, XSD.decimal,
        XSD.boolean,
        XSD.date, XSD.dateTime,
        XSD.string,
    ]
    ranges = list(ranges)
    # exact match
    for p in priority:
        if p in ranges:
            return XSD_TO_MERMAID.get(p, DEFAULT_MERMAID_TYPE)
    # fallback to first known
    for r in ranges:
        if r in XSD_TO_MERMAID:
            return XSD_TO_MERMAID[r]
    return DEFAULT_MERMAID_TYPE

# ---------- Extraction from rdflib graph ----------

def extract_classes(g: Graph) -> Set[URIRef]:
    classes = set(g.subjects(RDF.type, OWL.Class))
    # Also consider rdfs:Class tags (sometimes ontologies use this)
    classes |= set(g.subjects(RDF.type, RDFS.Class))
    return classes

def extract_datatype_properties(g: Graph) -> List[URIRef]:
    return list(g.subjects(RDF.type, OWL.DatatypeProperty))

def extract_object_properties(g: Graph) -> List[URIRef]:
    return list(g.subjects(RDF.type, OWL.ObjectProperty))

def all_domains(g: Graph, prop: URIRef) -> Set[URIRef]:
    return set(g.objects(prop, RDFS.domain))

def all_ranges(g: Graph, prop: URIRef) -> Set[URIRef]:
    return set(g.objects(prop, RDFS.range))

# ---------- Mermaid builder ----------

def build_mermaid(
    g: Graph,
    include_untyped_domain_range_classes: bool = True,
) -> str:
    """
    Produce a Mermaid diagram in the same style as your earlier example.
    - graph TD
    - Node blocks with <br/>-separated datatype properties
    - Edges labeled by object property names
    """

    # Collect classes
    classes = set(extract_classes(g))
    #print("CLASSES:  ", classes)
    # Collect datatype properties per class
    # class_iri -> { prop_name: type_str }
    class_attrs: Dict[URIRef, Dict[str, str]] = defaultdict(dict)

    for dp in extract_datatype_properties(g):
        domains = all_domains(g, dp) or set()  # may be empty
        ranges = all_ranges(g, dp) or set([XSD.string])
        # Filter only XSD datatypes
        xsd_ranges = {r for r in ranges if str(r).startswith(str(XSD))}
        if not xsd_ranges:
            xsd_ranges = set([XSD.string])

        # Map the property to Mermaid type
        mermaid_type = first_mermaid_type(xsd_ranges)
        prop_name = local_name(dp, fallback_prefix="DP")

        if not domains:
            # No explicit domain — you may choose to skip or attach to a pseudo class
            # Here, we skip adding attributes without domain to any node.
            continue

        for d in domains:
            classes.add(d)
            class_attrs[d][prop_name] = mermaid_type

    #print("ATTRS:  ", class_attrs)
    # Collect object properties as edges
    edges: List[Tuple[URIRef, URIRef, str]] = []  # (src, tgt, label)

    for op in extract_object_properties(g):
        label = local_name(op, fallback_prefix="OP")
        domains = all_domains(g, op)
        ranges = all_ranges(g, op)

        # Only keep class-like ranges/domains
        # If they’re missing, we don’t create edges (can’t draw them meaningfully).
        if not domains or not ranges:
            continue

        for d in domains:
            if include_untyped_domain_range_classes:
                classes.add(d)
            for r in ranges:
                if include_untyped_domain_range_classes:
                    classes.add(r)
                edges.append((d, r, label))

    #print("EDGES:  ", edges)

    # Build node section
    # Mermaid node with attribute lines using <br/>
    node_lines: List[str] = []
    for cls in sorted(classes, key=lambda x: local_name(x).lower()):
        cid = local_name(cls)
        # Node header text
        label_lines = [cid]
        # sorted attributes for determinism
        attrs = class_attrs.get(cls, {})
        if attrs:
            for pname in sorted(attrs):
                label_lines.append(f"{pname}: {attrs[pname]}")
        # join with <br/>
        label_text = "<br/>".join(label_lines)
        node_lines.append(f'{cid}["{label_text}"]')

    #print("NODE_LINES:  ", node_lines)

    # Build edges section
    edge_lines: List[str] = []
    for src, tgt, lab in sorted(
        edges,
        key=lambda t: (local_name(t[0]).lower(), local_name(t[1]).lower(), t[2].lower()),
    ):
        s = local_name(src)
        t = local_name(tgt)
        edge_lines.append(f"{s} -->|{lab}| {t}")

    #print("EDGE_LINES:  ", edge_lines)

    # Compose mermaid
    lines: List[str] = []
    lines.append("graph TD")
    lines.append("%% Nodes")
    lines.extend(node_lines)
    lines.append("")
    lines.append("%% Relationships")
    lines.extend(edge_lines)
    lines.append("")
    lines.append("%% Styling (none; generated script ignores styles)")
    return "\n".join(lines) + "\n"

# ---------- CLI / Example ----------

def ontology_ttl_to_mermaid(ttl_path: str) -> str:
    g = Graph()
    g.parse(ttl_path, format="turtle")
    return build_mermaid(g)

if __name__ == "__main__":

    mermaid = ontology_ttl_to_mermaid("ontos/sales-onto.ttl")
    with open("ontos/sales-onto.mermaid", "w", encoding="utf-8") as f:
        f.write(mermaid)
        print(mermaid)
