"""Load .txt documents from a directory and upsert them into a Chroma collection."""
import os

from rag.chunking import chunk_text
from rag.config import DEFAULT_COLLECTION, DEFAULT_DB_PATH, DEFAULT_DOCS_DIR
from rag.store import get_collection
from rag.structured_chunking import chunk_document

CHUNKING_STRATEGIES = ("fixed", "structured")


def load_documents(docs_dir: str, strategy: str = "fixed") -> tuple[list[str], list[str], list[dict]]:
    """Read every .txt file in docs_dir and chunk it into ids/docs/metadatas.

    strategy: "fixed" uses chunk_text()'s fixed-width slicing (baseline).
    "structured" uses the section/clause-aware chunker in structured_chunking.py.
    """
    if strategy not in CHUNKING_STRATEGIES:
        raise ValueError(f"Unknown chunking strategy '{strategy}'. Choose from {CHUNKING_STRATEGIES}.")

    ids, docs, metadatas = [], [], []
    for fname in sorted(os.listdir(docs_dir)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(docs_dir, fname)
        with open(path, encoding="utf-8") as f:
            text = f.read()

        if strategy == "structured":
            chunks_with_metadata = chunk_document(text, fname)
        else:
            chunks_with_metadata = [(chunk, {"source": fname, "chunk": i})
                                     for i, chunk in enumerate(chunk_text(text))]

        for i, (chunk, metadata) in enumerate(chunks_with_metadata):
            ids.append(f"{fname}::{i}")
            docs.append(chunk)
            metadatas.append(metadata)

    return ids, docs, metadatas


def ingest(docs_dir: str = DEFAULT_DOCS_DIR, db_path: str = DEFAULT_DB_PATH,
           collection_name: str = DEFAULT_COLLECTION, strategy: str = "fixed") -> int:
    """Chunk and upsert all .txt files in docs_dir. Returns the number of chunks ingested."""
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"docs directory '{docs_dir}' does not exist.")

    ids, docs, metadatas = load_documents(docs_dir, strategy)
    if not docs:
        return 0

    collection = get_collection(db_path, collection_name)
    collection.upsert(ids=ids, documents=docs, metadatas=metadatas)
    return len(docs)
