"""Synthesize a final answer from retrieved context across all sub-queries."""
from openai import OpenAI

from core.config import MODEL


def _citation_label(metadata: dict) -> str:
    """Build a human-readable source label from whatever metadata the
    ingestion strategy attached. Structured chunks get a doc/section/clause
    label; fixed chunks fall back to source filename + chunk index."""
    source = metadata.get("source", "unknown")
    doc_title = metadata.get("doc_title")
    section_number = metadata.get("section_number")
    clause_id = metadata.get("clause_id")

    if doc_title:
        label = doc_title
        if clause_id:
            label += f", clause {clause_id}"
        elif section_number:
            label += f", section {section_number}"
        return f"{label} ({source})"

    chunk = metadata.get("chunk")
    return f"{source}, chunk {chunk}" if chunk is not None else source


def synthesize(client: OpenAI, query: str, subqueries: list[str],
                retrieved: dict[str, list[dict]]) -> str:
    """Combine retrieved context across all sub-queries into a final answer."""
    context_blocks = []
    for sq in subqueries:
        chunks = retrieved.get(sq, [])
        if not chunks:
            continue
        joined = "\n---\n".join(
            f"[Source: {_citation_label(c['metadata'])}]\n{c['text']}" for c in chunks
        )
        context_blocks.append(f"Sub-question: {sq}\nRetrieved context:\n{joined}")

    context_text = "\n\n".join(context_blocks) if context_blocks else "(no relevant context retrieved)"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer the user's original question using only the retrieved "
                    "context provided below. If the context is insufficient to fully "
                    "answer, say so explicitly rather than guessing. Cite the "
                    "[Source: ...] label(s) supporting each claim you make."
                ),
            },
            {
                "role": "user",
                "content": f"Original question: {query}\n\n{context_text}",
            },
        ],
    )
    return response.choices[0].message.content
