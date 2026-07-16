"""Agentic RAG orchestration: decompose -> retrieve -> synthesize."""
from openai import OpenAI

from core.config import DEFAULT_COLLECTION, DEFAULT_DB_PATH
from core.decompose import decompose_query
from core.retrieval import retrieve
from core.store import get_collection
from core.synthesis import synthesize


def run(query: str, db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION) -> str:
    client = OpenAI()
    collection = get_collection(db_path, collection_name)

    if collection.count() == 0:
        print(f"Warning: collection '{collection_name}' at '{db_path}' is empty. "
              f"Run ingest.py first, or answers will have no retrieved context.")

    print("Decomposing query...")
    subqueries = decompose_query(client, query)
    for i, sq in enumerate(subqueries, 1):
        print(f"  {i}. {sq}")

    print("Retrieving context from Chroma...")
    retrieved = retrieve(collection, subqueries)

    print("Synthesizing answer...\n")
    return synthesize(client, query, subqueries, retrieved)
