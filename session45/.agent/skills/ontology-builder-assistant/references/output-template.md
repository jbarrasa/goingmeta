# Output template

Use this structure in the final answer.

## 1. CQ-to-ontology mapping

For each competency question or explicit requirement, use a compact block like this:

- **CQ-1**: [question]
  - **Needed ontology elements**: ClassA, ClassB, propertyC, valueD
  - **Why needed**: [one short explanation]
  - **Exclusions / gaps**: [optional]

## 2. Top-level disjoint class scheme

- **Scheme chosen**: [list top-level classes]
- **Why this scheme fits**: [1-3 sentences]
- **Disjointness**: `DisjointClasses(...)` or the equivalent in the requested formalism
- **Branch assignment**:
  - ClassA -> TopLevel1
  - ClassB -> TopLevel2

## 3. Class definitions

Use one subsection per class.

### ClassName
- **Parent**: ParentClass
- **Definition**: An ClassName is a ParentClass that ...
- **Inclusion justification**: required by [CQ/requirement], supported by [sample-data signal]
- **Necessary properties**:
  - `propertyName`: [clear description]

## 4. Final ontology serialization

Default to Turtle unless the user explicitly requests a different syntax.
