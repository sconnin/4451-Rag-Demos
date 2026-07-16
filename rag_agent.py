"""CLI: agentic RAG query over a Chroma collection (decompose -> retrieve -> synthesize)."""
import argparse
import sys

from rag.config import DEFAULT_DB_PATH, collection_name
from rag.pipeline import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic RAG query over a Chroma collection.")
    parser.add_argument("query", nargs="?", help="The question to ask")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--collection", default=None,
                         help="Chroma collection to query (default: 'documents_fixed', matching "
                              "ingest.py's default chunking strategy; pass 'documents_structured' "
                              "to query docs ingested with --chunking structured)")
    args = parser.parse_args()

    collection = args.collection or collection_name("fixed")

    query = args.query
    if not query:
        if sys.stdin.isatty():
            query = input("Enter your question: ").strip()
        else:
            query = sys.stdin.read().strip()

    if not query:
        print("No query provided.")
        sys.exit(1)

    answer = run(query, args.db_path, collection)
    print(answer)


if __name__ == "__main__":
    main()
