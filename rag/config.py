"""Shared defaults for the ingestion and query pipelines."""
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DOCS_DIR = "./data"
DEFAULT_DB_PATH = "./chroma_db"
DEFAULT_COLLECTION = "documents"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

MODEL = "gpt-5-mini"


def collection_name(strategy: str, base: str = DEFAULT_COLLECTION) -> str:
    """Per-strategy collection name, e.g. 'documents_fixed', 'documents_structured'.

    Keeps chunks from different chunking strategies in separate Chroma
    collections so re-ingesting with a different strategy can't silently
    overwrite or mix with chunks from another strategy.
    """
    return f"{base}_{strategy}"
