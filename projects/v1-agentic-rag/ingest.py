"""CLI: chunk .txt files in a directory and upsert them into a Chroma collection."""
import argparse
import sys

from core.config import DEFAULT_DB_PATH, DEFAULT_DOCS_DIR, collection_name
from core.ingestion import CHUNKING_STRATEGIES, ingest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest .txt files into a Chroma collection.")
    parser.add_argument("docs_dir", nargs="?", default=DEFAULT_DOCS_DIR,
                         help=f"Directory of .txt files (default: {DEFAULT_DOCS_DIR})")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Chroma persistent storage path")
    parser.add_argument("--collection", default=None,
                         help="Chroma collection name (default: '<documents>_<chunking>', "
                              "e.g. 'documents_fixed' or 'documents_structured', so different "
                              "chunking strategies never share a collection)")
    parser.add_argument("--chunking", choices=CHUNKING_STRATEGIES, default="fixed",
                         help="Chunking strategy: 'fixed' (baseline, default) or "
                              "'structured' (section/clause-aware)")
    args = parser.parse_args()

    collection = args.collection or collection_name(args.chunking)

    try:
        count = ingest(args.docs_dir, args.db_path, collection, args.chunking)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if count == 0:
        print(f"No .txt files found in '{args.docs_dir}'. Nothing ingested.")
        return

    print(f"Ingested {count} chunks from '{args.docs_dir}' into collection "
          f"'{collection}' at '{args.db_path}'.")


if __name__ == "__main__":
    main()
