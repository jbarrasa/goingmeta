# Modeling checklist

Use this checklist before finalizing the ontology.

## Inclusion test

Every included element must pass both tests:

1. requirement test: needed by an explicit requirement or competency question. If not, exclude the element and mention the exclusion briefly.
2. evidence test: supported by representative data. If the the element is required by 1 but no supported data is found in the samples, mention it briefly.


## Depth test

- maximum taxonomy depth: 3
- prefer properties over subclasses
- add a third level only when a competency question or mapping task requires it

## Grounding test

- choose a small top-level grounding scheme
- keep top-level classes mutually disjoint
- assign each included class to one grounding branch

## Serialization test

- include only final included classes and properties
- assert top-level disjointness
- avoid speculative axioms
- add domain/range only when stable and useful

## Definition test

- every class gets an informative definition
- use Aristotelian form when possible
- avoid circular or generic wording
