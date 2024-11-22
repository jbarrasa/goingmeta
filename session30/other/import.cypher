with $jsondata as value

// Create the Agreement node
MERGE (agreement:Agreement {
    agreement_type: value.agreement.agreement_type,
    contract_id: value.agreement.contract_id,
    effective_date: value.agreement.effective_date,
    expiration_date: value.agreement.expiration_date,
    renewal_term: value.agreement.renewal_term,
    name: value.agreement.name
})

// Create the Country and Governed By Law relationship
MERGE (country:Country {name: value.governed_by_law.country.name})
MERGE (agreement)-[:GOVERNED_BY_LAW]->(country)

// Create Party nodes and relationships
WITH value, agreement
UNWIND value.parties AS party
MERGE (org:Organization {name: party.name, role: party.role})
MERGE (country:Country {name: party.incorporated_in.country.name})
MERGE (org)-[:INCORPORATED_IN]->(country)
MERGE (org)-[:IS_PARTY_TO]->(agreement)

// Create Clause nodes and relationships
WITH value, agreement
UNWIND value.clauses AS clause
MERGE (contractClause:ContractClause {name: clause.name})
MERGE (clauseType:ClauseType {name: clause.clause_type})
MERGE (contractClause)-[:HAS_TYPE]->(clauseType)
MERGE (agreement)-[:HAS_CLAUSE]->(contractClause)

// Create Excerpt nodes and relationships
WITH clause, contractClause
UNWIND clause.excerpts AS excerpt
MERGE (excerptNode:Excerpt {text: excerpt.text})
MERGE (contractClause)-[:HAS_EXCERPT]->(excerptNode);