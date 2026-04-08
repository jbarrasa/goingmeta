"""
run_kg_pipeline.py

Build a knowledge graph from clinical-case text files using SimpleKGPipeline
driven by a pre-built GraphSchema JSON file.

Prerequisites
─────────────
  pip install neo4j-graphrag openai rdflib

Environment variables required
───────────────────────────────
  NEO4J_URI       – e.g. bolt://localhost:7687
  NEO4J_USER      – e.g. neo4j
  NEO4J_PASSWORD  – your Neo4j password
  OPENAI_API_KEY  – your OpenAI key

Usage
─────
  python run_kg_pipeline.py clinical_case_sheet.json
"""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.experimental.components.schema import GraphSchema
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import OpenAILLM


# ── Paths ──────────────────────────────────────────────────────────────────────

_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGIES_DIR = _ROOT / "ontology"
DATA_DIR = _ROOT / "data"

# ── Configuration ──────────────────────────────────────────────────────────────

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "neoneoneo")

# Model used for entity extraction.  gpt-4o supports structured output v2.
EXTRACTION_MODEL = "gpt-4o"
# Model used for generating text embeddings.
EMBEDDING_MODEL = "text-embedding-3-small"


async def main(schema_file: str) -> None:

    # ── 1. Load schema from JSON ───────────────────────────────────────────────
    schema_path = ONTOLOGIES_DIR / schema_file
    print(f"Loading schema from {schema_path} …")
    schema = GraphSchema.from_file(str(schema_path))

    # ── 2. Set up the LLM ──────────────────────────────────────────────────────
    # OpenAI structured output v2: pass response_format={"type": "json_object"}
    # so the model is constrained to emit valid JSON.  neo4j-graphrag's
    # EntityRelationExtractor wraps this into the prompt / parsing logic.
    llm = OpenAILLM(
        model_name=EXTRACTION_MODEL,
        model_params={
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
    )

    # ── 3. Set up the embedder ─────────────────────────────────────────────────
    embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # ── 4. Connect to Neo4j ────────────────────────────────────────────────────
    driver = neo4j.GraphDatabase.driver(
        NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), database="medical"
    )

    # ── 5. Build the pipeline ──────────────────────────────────────────────────
    pipeline = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        schema=schema,
        from_pdf=False,
        perform_entity_resolution=True,
    )

    # ── 6. Iterate over all documents in the data folder ──────────────────────
    doc_files = sorted(DATA_DIR.glob("*.txt"))
    print(f"\nFound {len(doc_files)} document(s) in {DATA_DIR}\n")

    for doc_path in doc_files:
        text = doc_path.read_text(encoding="utf-8")
        print(f"Processing {doc_path.name} ({len(text)} chars) …")
        result = await pipeline.run_async(text=text)
        print(f"  result: {result}\n")

    driver.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the KG pipeline over all files in the data folder."
    )
    parser.add_argument(
        "schema_file",
        help="Name of the GraphSchema JSON file in the ontologies folder (e.g. clinical_case_sheet.json)",
    )
    args = parser.parse_args()
    asyncio.run(main(args.schema_file))
