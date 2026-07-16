"""Retrieve context chunks from a Chroma collection for each sub-query."""
from chromadb.api.models.Collection import Collection


def retrieve(collection: Collection, subqueries: list[str],
             n_results: int = 4) -> dict[str, list[dict]]:
    """Query the Chroma collection once per sub-query; dedupe returned chunks.

    Each result is {"text": chunk_text, "metadata": {...}} — metadata carries
    whatever the ingestion strategy attached (e.g. "source"/"chunk" for the
    fixed chunker, or "doc_title"/"section_number"/"clause_id" for the
    structured chunker), which synthesis.py uses for citations.
    """
    results: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for sq in subqueries:
        res = collection.query(query_texts=[sq], n_results=n_results)
        docs = res.get("documents", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        if len(metadatas) != len(docs):
            raise ValueError(
                f"Chroma returned {len(docs)} documents but {len(metadatas)} metadatas "
                f"for sub-query {sq!r}; results would be misaligned."
            )
        unique = []
        for doc, metadata in zip(docs, metadatas):
            if doc not in seen:
                seen.add(doc)
                unique.append({"text": doc, "metadata": metadata or {}})
        results[sq] = unique
    return results
