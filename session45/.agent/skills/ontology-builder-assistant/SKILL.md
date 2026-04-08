---
name: ontology-builder-assistant
description: derive a minimal reusable ontology from purpose statements, competency questions, sample data, reusable vocabularies, supporting semantic evidence, and implementation constraints. use when you're asked to draft an ontology for a specific use case. Especially useful for ontology bootstrapping, information extraction schemas, mapping-oriented semantic models, and defensible cq-to-model traceability with final serialization.
---

# Ontology Builder Assistant

## Overview

Derive a small reusable ontology that is purpose-led, evidence-backed, and aggressively scoped.
Treat the use case description and competency questions as the semantic blueprint. Treat sample data as evidence for inclusion, not as the ontology boundary.

## Required behavior

Follow this workflow in order.

### 1. Normalize the inputs

Extract and organize whatever is available into these buckets. 

- purpose: intended users or consumers, use cases, scope boundaries, competency questions, assumptions, constraints
- representative data, structured or unstructrued. Typically structured data will be presented in the form of csv files or json/xml/yaml. Unstructured data will be presented as doucments in natural language. They can be of any nature (manuals, reports, contracts, etc.) 
- existing ontologies, vocabularies, or ontology design patterns that can be reused fully or partially to avoid reinventing the wheel. 
- supporting semantic evidence such as glossary terms, documentation, data catalog descriptions or SME notes
- implementation and validation constraints such as formalism, naming rules, reasoning profile, test expectations, and quality criteria

When a bucket is missing or thin, say so explicitly and describe how the gap affects the ontology design before proceeding with the available inputs and get confirmation from the user.
Do not invent requirements to fill gaps.

### 2. Build the requirement gate

Create a candidate list of classes, properties, and controlled values from:

- explicit use cases
- explicit scope statements
- competency questions
- implementation constraints that force representational choices

Treat competency questions as the strongest filter.
An ontology element is eligible only if it is required to answer at least one competency question or explicit requirement.

### 3. Build the evidence gate

Check each candidate against the representative data.
Support can be direct or near-direct evidence from the samples, such as:

- repeated entities or record types
- repeated attributes or columns
- events, roles, states, measures, identifiers, dates, places, relationships, document structures, or lexical patterns
- examples in documents that an extraction model or mapping would need to capture

Generalize beyond literal sample mentions when doing so creates a reusable class or property, but only when the generalization is still supported by the data.
Assume the provided sample is incomplete. For unstructured sources, expect similar documents; for structured sources, expect additional records.

### 4. Apply strict inclusion and exclusion rules

Include an ontology element only when both conditions hold:

1. it is required by at least one explicit requirement or competency question
2. it is supported by the sample data

Exclude everything else, even if it appears in a reused vocabulary, in domain background material, or seems generally useful.
Do not expand the model for elegance, completeness, future possibilities, or encyclopedic coverage.

### 5. Choose a top-level grounding scheme

Create a small set of top-level mutually disjoint grounding classes that reduces cross-category confusion.
Choose and adapt a domain-appropriate pattern such as (take them as guidance, not as enforced templates):

- person, object, location, event
- temporal_entity, spacetime_volume, dimension, place, persistent_item, time_span
- asset_artifact, data_information, governance, location, measurement, party, process_event, state_condition, time
- another similarly practical top-level scheme

Rules:

- keep the set small and useful
- declare the top-level classes mutually disjoint
- place each included class under exactly one grounding branch unless a different design is explicitly required
- explain why this grounding scheme fits the use case

### 6. Keep the taxonomy shallow and extraction-friendly

Apply these modeling constraints:

- maximum class depth is 3
- prefer properties over deeper subclass trees
- add a third level only when clearly necessary for the competency questions or mapping/extraction task
- use potential subclasses beyond level 3 to create few shot examples added to a (multivalued) property associated to the class. Use rdfs:comment or   skos:example prefixing the value with "examle: " to make it clear that the value is an example and not a controlled value.
- keep names concrete and operational
- make the ontology reusable, but concrete enough for information extraction from unstructured text or mapping from structured data

### 7. Reuse external vocabularies carefully

Reuse classes or properties from existing ontologies only when reuse helps satisfy an included requirement.
Do not import large fragments that violate the minimal-scope rule.
Map reused terms into the final ontology narrative so the output remains understandable on its own.
When reuse is partial, say what was reused and what was deliberately not reused.

### 8. Define classes and properties clearly

Provide an Aristotelian definition for every class whenever possible, in the form:

- “an x is a y that z.”

Also define properties and other modeled elements with informative, disambiguating descriptions.
Avoid circular definitions and vague labels.
Definitions must help distinguish nearby concepts that might be confused during extraction or mapping.

### 9. Validate before producing the final ontology

Run the checks in `references/modeling-checklist.md` before finalizing the ontology.
If the model fails any check, fix the problem and re-run the checklist before proceeding.

## Output contract

Return the result in exactly these four sections and follow the structure defined in `references/output-template.md`.

### 1. CQ-to-ontology mapping

For each competency question, provide:

- the cq text or a concise identifier
- the ontology classes, properties, and controlled values needed to answer it
- a short note on why each element is required
- any important exclusions or unresolved gaps

If there are explicit requirements that are not phrased as competency questions, include them in the same section under a clearly labeled requirements subsection.

### 2. Top-level disjoint class scheme

Provide:

- the chosen grounding classes
- a one-line rationale for the scheme
- the mutual disjointness statement
- a short mapping from each included class to one grounding class

### 3. Class definitions

For every included class, provide:

- preferred label
- parent class
- definition
- inclusion justification: cite the requirement or cq and the supporting sample-data signal
- key properties that are necessary for the use case

You may also define essential properties in this section when that improves clarity.

### 4. Final ontology serialization

Serialise only the final included ontology.
Follow RDFS and minimally OWL to differentiate relationships from attributes (owl:ObjectProperty vs owl:DatatypeProperty respectively) and for any additional construct when strictly needed.
Serialise in turtle syntax.

When serializing:

- include prefixes
- declare classes and required properties only
- assert top-level disjointness
- keep axioms minimal and practical
- add domains and ranges as much as possible but make sure they are stable enough to help the use case
- avoid speculative restrictions and avoid ornamental axioms

### 5. Translate the ontology into actionable artifacts
 
#### If the sample data contains unstructured documents:
Generate a `GraphSchema` JSON file that can be used to extract the modeled concepts and relationships using a large language model: 
After writing the ontology `.ttl` file, run the bundled conversion script
`scripts/owl_to_graphrag_schema.py` (located in the same directory as this
skill) passing the `.ttl` path as the positional argument. The script writes
a `GraphSchema` JSON file alongside the ontology using the same stem and
`.json` extension. Pass `--out <path>` to override the output location.

Dependencies: `rdflib`, `neo4j-graphrag`.

Confirm the JSON was written and report the node type count, relationship type
count, and pattern count to the user.
#### If the sample data contains structured documents:
Generate a mapping specification that can be used to map the structured data to the ontology. The mapping specification should include:
- a mapping from each column or field in the structured data to the corresponding class or property in the ontology
- any necessary transformations or normalization rules for the data
- examples of how to apply the mapping to the structured data

## Style and decision rules

- be explicit about what was excluded and why, but keep exclusions concise
- never let sample-data details force an overly narrow ontology boundary
- never let domain background knowledge broaden the ontology beyond the stated purpose
- prefer a model that is defensible and traceable over one that is comprehensive
- when the evidence is ambiguous, choose the smaller ontology and explain the tradeoff
