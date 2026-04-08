"""
owl_to_graphrag_schema.py

Converts an OWL/Turtle ontology to a neo4j-graphrag GraphSchema.

Rules applied:
- Only *leaf* OWL classes (no subclasses) become NodeTypes.
- Only *leaf* ObjectProperties (no sub-properties) become RelationshipTypes.
- domain / range expressions that use owl:unionOf are expanded to their members.
- Non-leaf domain / range classes are replaced with their leaf descendants.
- Datatype properties declared on a parent class are inherited by each leaf
  subclass.

CLI usage
─────────
  # write schema JSON next to the ontology (same stem, .json extension)
  python owl_to_graphrag_schema.py ontology/clinical_case.ttl

  # explicit output path
  python owl_to_graphrag_schema.py ontology/clinical_case.ttl --out schema.json
"""

from __future__ import annotations

import asyncio
import argparse
from pathlib import Path
from typing import Any

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS, XSD

from neo4j_graphrag.experimental.components.schema import (
    GraphSchema,
    NodeType,
    PropertyType,
    RelationshipType,
    SchemaBuilder,
)


# ── XSD → graphrag PropertyType ───────────────────────────────────────────────

_XSD_TO_PROPERTY_TYPE: dict[str, str] = {
    str(XSD.string): "STRING",
    str(XSD.normalizedString): "STRING",
    str(XSD.token): "STRING",
    str(XSD.integer): "INTEGER",
    str(XSD.int): "INTEGER",
    str(XSD.long): "INTEGER",
    str(XSD.short): "INTEGER",
    str(XSD.byte): "INTEGER",
    str(XSD.nonNegativeInteger): "INTEGER",
    str(XSD.positiveInteger): "INTEGER",
    str(XSD.float): "FLOAT",
    str(XSD.double): "FLOAT",
    str(XSD.decimal): "FLOAT",
    str(XSD.boolean): "BOOLEAN",
    str(XSD.date): "DATE",
    str(XSD.dateTime): "ZONED_DATETIME",
    str(XSD.duration): "DURATION",
    str(XSD.time): "ZONED_TIME",
}

_DEFAULT_PROPERTY_TYPE = "STRING"


def _xsd_to_property_type(xsd_type: URIRef) -> str:
    return _XSD_TO_PROPERTY_TYPE.get(str(xsd_type), _DEFAULT_PROPERTY_TYPE)


# ── Low-level RDF helpers ──────────────────────────────────────────────────────

def _local_name(uri: URIRef) -> str:
    """Return the local part of a URI (after the last # or /)."""
    s = str(uri)
    for sep in ("#", "/"):
        idx = s.rfind(sep)
        if idx != -1:
            return s[idx + 1:]
    return s


def _first_literal(g: Graph, subject: URIRef, predicate: URIRef) -> str:
    return str(next(g.objects(subject, predicate), ""))


def _expand_union(g: Graph, node: Any) -> list[URIRef]:
    """Return the URIRef members of an owl:unionOf blank node, or [node] if
    node is already a URIRef."""
    if isinstance(node, URIRef):
        return [node]
    if not isinstance(node, BNode):
        return []
    union_list = next(g.objects(node, OWL.unionOf), None)
    if union_list is None:
        return []
    members: list[URIRef] = []
    current = union_list
    while current and current != RDF.nil:
        first = next(g.objects(current, RDF.first), None)
        if isinstance(first, URIRef):
            members.append(first)
        current = next(g.objects(current, RDF.rest), None)
    return members


# ── Hierarchy helpers ──────────────────────────────────────────────────────────

def _leaf_classes(g: Graph) -> set[URIRef]:
    """Classes that are not the superclass of any other class."""
    all_classes: set[URIRef] = {
        s for s in g.subjects(RDF.type, OWL.Class) if isinstance(s, URIRef)
    }
    parents: set[URIRef] = {
        o
        for _, _, o in g.triples((None, RDFS.subClassOf, None))
        if isinstance(o, URIRef)
    }
    return all_classes - parents


def _leaf_object_properties(g: Graph) -> set[URIRef]:
    """ObjectProperties that are not the super-property of any other property."""
    all_props: set[URIRef] = {
        s for s in g.subjects(RDF.type, OWL.ObjectProperty) if isinstance(s, URIRef)
    }
    parents: set[URIRef] = {
        o
        for _, _, o in g.triples((None, RDFS.subPropertyOf, None))
        if isinstance(o, URIRef)
    }
    return all_props - parents


def _ancestors(g: Graph, cls: URIRef) -> list[URIRef]:
    """Return cls followed by all its superclasses (breadth-first)."""
    visited: list[URIRef] = []
    queue = [cls]
    seen: set[URIRef] = set()
    while queue:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        visited.append(current)
        for parent in g.objects(current, RDFS.subClassOf):
            if isinstance(parent, URIRef) and parent not in seen:
                queue.append(parent)
    return visited


def _expand_to_leaves(
    g: Graph, classes: list[URIRef], leaf_classes: set[URIRef]
) -> list[URIRef]:
    """Replace each class with its leaf descendants (or itself when already a leaf).
    The returned list preserves encounter order and is deduplicated."""
    result: list[URIRef] = []
    seen: set[URIRef] = set()

    def collect(cls: URIRef) -> None:
        if cls in leaf_classes:
            if cls not in seen:
                seen.add(cls)
                result.append(cls)
            return
        for sub in g.subjects(RDFS.subClassOf, cls):
            if isinstance(sub, URIRef):
                collect(sub)

    for c in classes:
        collect(c)
    return result


# ── Property collection ────────────────────────────────────────────────────────

def _properties_for_class(
    g: Graph, cls: URIRef, leaf_classes: set[URIRef]
) -> list[PropertyType]:
    """Collect DatatypeProperties for *cls*, including those declared on
    ancestor classes (property inheritance)."""
    props: list[PropertyType] = []
    seen_names: set[str] = set()

    for ancestor in _ancestors(g, cls):
        for dp in sorted(
            g.subjects(RDF.type, OWL.DatatypeProperty), key=lambda x: _local_name(x)
        ):
            if not isinstance(dp, URIRef):
                continue
            raw_domains = list(g.objects(dp, RDFS.domain))
            if not raw_domains:
                continue
            expanded: set[URIRef] = set()
            for d in raw_domains:
                expanded.update(_expand_union(g, d))
            if ancestor not in expanded:
                continue
            name = _local_name(dp)
            if name in seen_names:
                continue
            seen_names.add(name)
            range_uri = next(g.objects(dp, RDFS.range), None)
            prop_type = (
                _xsd_to_property_type(range_uri)
                if isinstance(range_uri, URIRef)
                else _DEFAULT_PROPERTY_TYPE
            )
            props.append(
                PropertyType(
                    name=name,
                    type=prop_type,
                    description=_first_literal(g, dp, RDFS.comment),
                )
            )
    return props


# ── Public function ────────────────────────────────────────────────────────────

async def owl_to_graphrag_schema(path: str | Path) -> GraphSchema:
    """Parse an OWL/Turtle ontology at *path* and return a neo4j-graphrag
    GraphSchema.

    * Only leaf OWL classes become NodeTypes.
    * Only leaf ObjectProperties become RelationshipTypes.
    * Union domains/ranges are expanded; non-leaf classes are replaced by their
      leaf descendants when building pattern triples.
    * DatatypeProperties on parent classes are inherited by leaf subclasses.
    """
    g = Graph()
    g.parse(str(path))

    leaves = _leaf_classes(g)
    leaf_ops = _leaf_object_properties(g)

    # ── NodeTypes ──────────────────────────────────────────────────────────────
    node_types: list[NodeType] = [
        NodeType(
            label=_local_name(cls),
            description=_first_literal(g, cls, RDFS.comment),
            properties=_properties_for_class(g, cls, leaves),
        )
        for cls in sorted(leaves, key=_local_name)
    ]

    # ── RelationshipTypes ──────────────────────────────────────────────────────
    rel_types: list[RelationshipType] = [
        RelationshipType(
            label=_local_name(op),
            description=_first_literal(g, op, RDFS.comment),
            properties=[],
        )
        for op in sorted(leaf_ops, key=_local_name)
    ]

    # ── Patterns ───────────────────────────────────────────────────────────────
    patterns: list[tuple[str, str, str]] = []
    for op in sorted(leaf_ops, key=_local_name):
        rel_label = _local_name(op)

        raw_domains = list(g.objects(op, RDFS.domain))
        raw_ranges = list(g.objects(op, RDFS.range))

        domain_uris: list[URIRef] = []
        for d in raw_domains:
            domain_uris.extend(_expand_union(g, d))

        range_uris: list[URIRef] = []
        for r in raw_ranges:
            range_uris.extend(_expand_union(g, r))

        leaf_domains = _expand_to_leaves(g, domain_uris, leaves)
        leaf_ranges = _expand_to_leaves(g, range_uris, leaves)

        for d in leaf_domains:
            for r in leaf_ranges:
                patterns.append((_local_name(d), rel_label, _local_name(r)))

    return await SchemaBuilder().run(
        node_types=node_types,
        relationship_types=rel_types,
        patterns=patterns,
    )


# ── CLI entry point ────────────────────────────────────────────────────────────

async def _cli(ontology: Path, out: Path) -> None:
    print(f"Parsing {ontology} …")
    schema = await owl_to_graphrag_schema(ontology)
    schema.save(str(out), overwrite=True)
    print(f"Schema written to {out}")
    print(f"  NodeTypes ({len(schema.node_types)}): {[n.label for n in schema.node_types]}")
    print(f"  RelationshipTypes ({len(schema.relationship_types)}): {[r.label for r in schema.relationship_types]}")
    print(f"  Patterns: {len(schema.patterns)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert an OWL/Turtle ontology to a neo4j-graphrag schema JSON file."
    )
    parser.add_argument("ontology", type=Path, help="Path to the OWL/Turtle ontology file")
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON path (default: same folder and stem as the ontology, .json extension)",
    )
    args = parser.parse_args()

    ontology_path: Path = args.ontology
    out_path: Path = args.out or ontology_path.with_suffix(".json")

    asyncio.run(_cli(ontology_path, out_path))
