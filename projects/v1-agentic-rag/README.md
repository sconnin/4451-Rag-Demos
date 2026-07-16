# v1 — Agentic RAG (query decomposition + Chroma)

A basic agentic RAG pipeline: an OpenAI model (`gpt-5-mini`) decomposes a
complex question into sub-questions, each sub-question retrieves context
from a local Chroma collection, and the model synthesizes a final answer
from the combined context.

Built on the shared engine in [`core/`](../../core) — see the repo root
[README](../../README.md) for the overall monorepo structure and setup.

All commands below assume you're running from the **repo root** (not this
directory), so that `./data` and `./chroma_db` resolve correctly.

## Ingest documents

Put `.txt` files in a directory (default `./data`), then run:

```bash
python projects/v1-agentic-rag/ingest.py ./data
```

This chunks each file and upserts it into a persistent Chroma collection at
`./chroma_db` (using Chroma's built-in local embedding model — no embedding
API key required).

Two chunking strategies are available via `--chunking`:

- `fixed` (default) — baseline fixed-width chunking (`core/chunking.py`)
- `structured` — section/clause-aware chunking (`core/structured_chunking.py`)

Each strategy writes to its own Chroma collection by default
(`documents_fixed` / `documents_structured`), so re-ingesting the same docs
with a different strategy never overwrites or mixes chunks from the other:

```bash
python projects/v1-agentic-rag/ingest.py ./data --chunking fixed
python projects/v1-agentic-rag/ingest.py ./data --chunking structured
```

Pass `--collection` to override the default name for either strategy.

## Ask a question

```bash
python projects/v1-agentic-rag/rag_agent.py "your complex, multi-part question"
```

Queries `documents_fixed` by default. To query the structured-chunking
collection instead:

```bash
python projects/v1-agentic-rag/rag_agent.py "your question" --collection documents_structured
```

Or run without an argument to be prompted interactively. The script prints
the decomposed sub-questions, then the final synthesized answer.

## Retrieval

Retrieval is pure semantic (dense-vector) similarity via Chroma's default
local embedding model — no lexical/keyword matching or re-ranking stage.

## Files

- `ingest.py` — CLI: chunks and loads `.txt` files into Chroma
- `rag_agent.py` — CLI: decompose → retrieve → synthesize pipeline
