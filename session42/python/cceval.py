import os
import json
import textwrap
from typing import List
from openai import OpenAI


def format_cq_block(questions: List[str]) -> str:
    return "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))


def evaluate_ontology_against_cq(
    ontology_text: str,
    questions: List[str],
    model: str = None,
) -> dict:
    client = OpenAI()
    model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini-2024-07-18")

    schema = {
        "name": "CQEval",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
                "per_cq": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "question":       {"type": "string"},
                            "score":          {"type": "number", "minimum": 0, "maximum": 1},
                            "reasoning":      {"type": "string"},
                            "suggestions":    {"type": "array", "items": {"type": "string"}},
                            "cypher_dataset": {"type": "string"},
                            "cypher_query":   {"type": "string"},
                        },
                        "required": ["question", "score", "reasoning", "suggestions",
                                     "cypher_dataset", "cypher_query"]
                    }
                },
                "global_suggestions": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["overall_score", "per_cq", "global_suggestions"]
        }
    }

    system_instructions = textwrap.dedent("""\
        You are an ontology QA assistant.
        Task: Given an OWL/RDFS ontology (as text) and a list of competency questions (CQs),
        judge how well the ontology could support answering each CQ.

        Map ontology classes to Neo4j node labels and object properties to relationships.

        -- Scoring (per CQ) --
        1.0 = ontology clearly models the required classes/properties/relationships. A query can be built to answer the CQ.
        0.5 = partially modeled; answerable only by applying minor refactoring first
        0.0 = not supported — critical modeling gaps

        For each CQ also provide:
        - cypher_dataset: a single Cypher CREATE statement seeding a minimal graph that
          should be sufficient to answer the CQ if the ontology supports it
        - cypher_query: a MATCH query implementing the CQ against that dataset

        Keep output terse and actionable.
    """)

    user_payload = textwrap.dedent(f"""\
        ONTOLOGY (OWL/RDFS):
        ---
        {ontology_text}
        ---
        COMPETENCY QUESTIONS:
        {format_cq_block(questions)}
    """)

    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_instructions},
            {"role": "user",   "content": user_payload},
        ],
        text={"format": {"type": "json_schema", **schema}},
    )

    out_text = resp.output_text if resp.output_text else resp.output[0].content[0].text
    return json.loads(out_text)


def run_empirical_check(
    cq_result: dict,
    neo4j_uri: str      = "<<DB ENDPOINT>>",
    neo4j_user: str     = "<<USER>>",
    neo4j_password: str = "<<PWD>>",
) -> list:
    """
    For each CQ: seeds a clean Neo4j graph with the generated dataset,
    runs the generated query, and records empirical results.
    Classifies as: fully_answered, not_answered, dataset_error, or query_error.
    """
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    results = []

    with driver.session() as session:
        for cq in cq_result["per_cq"]:
            session.run("MATCH (n) DETACH DELETE n")

            try:
                session.run(cq["cypher_dataset"])
            except Exception as e:
                results.append({"question": cq["question"], "status": "dataset_error", "error": str(e)})
                continue

            try:
                rows = session.run(cq["cypher_query"]).data()
                results.append({
                    "question":     cq["question"],
                    "llm_score":    cq["score"],
                    "status":       "fully_answered" if rows else "not_answered",
                    "result_count": len(rows),
                    "results":      rows,
                })
            except Exception as e:
                results.append({"question": cq["question"], "status": "query_error", "error": str(e)})

    driver.close()
    return results


# --- demo ---

ontology_text = """
@prefix ex:   <http://example.org/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .

ex:Person a owl:Class ; rdfs:label "Person" .

ex:hasParent a owl:ObjectProperty ;
  rdfs:domain ex:Person ; rdfs:range ex:Person ;
  rdfs:label "has parent" .

ex:hasChild a owl:ObjectProperty ;
  rdfs:domain ex:Person ; rdfs:range ex:Person ;
  owl:inverseOf ex:hasParent ;
  rdfs:label "has child" .
"""

questions = [
    "Can we retrieve all parents of a given person?",
    "Can we list all people who have at least two children?",
    "Can we find all diseases and their causative pathogens?",
]

result = evaluate_ontology_against_cq(ontology_text, questions)
print(json.dumps(result, indent=2))

# empirical check requires a running Neo4j instance
empirical = run_empirical_check(result)
print(json.dumps(empirical, indent=2))
