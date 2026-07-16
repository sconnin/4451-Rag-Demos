# 4451-Rag-Demos

Monorepo for a series of RAG (retrieval-augmented generation) projects that
build sequentially on one another. Each project reuses and extends a shared
core engine rather than re-implementing chunking, ingestion, and retrieval
from scratch.

## Structure

```
4451-Rag-Demos/
├── core/                    # shared RAG engine, imported as `core.*` by every project
│   ├── config.py            # shared defaults (paths, model, chunk size, collection naming)
│   ├── chunking.py          # baseline fixed-width chunking
│   ├── structured_chunking.py  # section/clause-aware chunking
│   ├── store.py             # Chroma client/collection access
│   ├── ingestion.py         # file loading + chunking + upsert
│   ├── decompose.py         # query decomposition
│   ├── retrieval.py         # per-sub-query Chroma retrieval
│   ├── synthesis.py         # final answer synthesis
│   └── pipeline.py          # orchestrates decompose -> retrieve -> synthesize
├── projects/
│   └── v1-agentic-rag/      # current project: query-decomposition agentic RAG
│       ├── ingest.py        # CLI: chunk + load documents into Chroma
│       ├── rag_agent.py     # CLI: decompose -> retrieve -> synthesize
│       └── README.md        # project-specific usage
├── data/                    # shared sample corpus (.txt files) used across projects
├── chroma_db/                # persistent Chroma store (gitignored)
├── pyproject.toml            # makes `core` importable via editable install
└── requirements.txt
```

## Versioning convention

- **`core/`** holds logic that is genuinely shared and stable across projects
  (chunking strategies, the Chroma store wrapper, retrieval, synthesis). It
  has no CLI of its own — it's a library, not an entrypoint.
- **`projects/vN-<name>/`** holds one versioned project: its CLI
  entrypoints, and a README describing what it adds relative to the
  previous version. Projects import from `core` rather than duplicating it.
- A new project starts as `projects/v{N+1}-<name>/` and either reuses
  `core` unchanged or extends it (new module in `core/`, or a new function/
  parameter on an existing one) if the new project needs shared capability
  the previous ones didn't. Breaking changes to `core` should be avoided
  once more than one project depends on it — prefer additive changes
  (new optional params, new modules) so older projects keep working.
- Projects do not depend on each other directly, only on `core`.

## Setup

```bash
pip install -r requirements.txt
pip install -e .        # makes `core` importable from any project directory
```

Authenticate with OpenAI by setting `OPENAI_API_KEY` in `.env` (already
gitignored), or via `export OPENAI_API_KEY=...`.

## Projects

- [`projects/v1-agentic-rag/`](projects/v1-agentic-rag/README.md) — query
  decomposition + Chroma retrieval + synthesis, with baseline (`fixed`) and
  section/clause-aware (`structured`) chunking strategies, each ingested
  into its own Chroma collection.

Run all project CLIs from the repo root (see each project's README for
exact commands), so relative paths like `./data` and `./chroma_db` resolve
consistently.
