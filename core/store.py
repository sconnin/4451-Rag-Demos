"""Chroma persistent client/collection access."""
import chromadb
from chromadb.api.models.Collection import Collection

from core.config import DEFAULT_COLLECTION, DEFAULT_DB_PATH


def get_collection(db_path: str = DEFAULT_DB_PATH,
                    collection_name: str = DEFAULT_COLLECTION) -> Collection:
    client = chromadb.PersistentClient(path=db_path)
    return client.get_or_create_collection(collection_name)
