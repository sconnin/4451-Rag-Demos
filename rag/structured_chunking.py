"""Structure-aware chunker for the policy documents in data/.

Unlike chunk_text() (fixed-width slicing), this respects the documents'
own boundaries: a title/"Updated"/date header block, bare-line section
headings, and numbered/lettered legal clauses ("1. ...", "a. ..."). Each
section/clause becomes one chunk; oversized clauses are split on sentence
boundaries and undersized ones are merged with their neighbor, so no unit
is ever cut mid-thought or left contextless.
"""
import re

MAX_CHUNK_CHARS = 900
MIN_CHUNK_CHARS = 80
SENTENCE_OVERLAP = 1

_NUMBERED_SECTION_RE = re.compile(r"^(\d+)\.\s+(.*)$")
_LETTERED_CLAUSE_RE = re.compile(r"^([a-z]{1,2})\.\s+(.*)$")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\"“])")


def _split_sentences(text: str) -> list[str]:
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    return [s for s in sentences if s]


def _split_oversized(text: str, max_chars: int = MAX_CHUNK_CHARS,
                      overlap: int = SENTENCE_OVERLAP) -> list[str]:
    """Split text into <= max_chars pieces on sentence boundaries, with a
    small sentence overlap so context carries across the split."""
    if len(text) <= max_chars:
        return [text]

    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return [text]

    pieces: list[str] = []
    current: list[str] = []
    current_len = 0
    for sentence in sentences:
        if current and current_len + len(sentence) + 1 > max_chars:
            pieces.append(" ".join(current))
            current = current[-overlap:] if overlap else []
            current_len = sum(len(s) + 1 for s in current)
        current.append(sentence)
        current_len += len(sentence) + 1
        # A carried-over sentence plus the new one can still exceed max_chars;
        # flush immediately rather than letting it grow further next iteration.
        if current_len > max_chars and len(current) > 1:
            pieces.append(" ".join(current))
            current, current_len = [], 0
    if current:
        pieces.append(" ".join(current))
    return pieces


def _is_heading(line: str) -> bool:
    """Heuristic: short, no terminal punctuation, not a numbered/lettered clause."""
    if not line or len(line) > 80:
        return False
    if line[-1] in ".;:,":
        return False
    if _NUMBERED_SECTION_RE.match(line) or _LETTERED_CLAUSE_RE.match(line):
        return False
    return True


_DATE_LINE_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d")


def _parse_header(lines: list[str]) -> tuple[str, list[str]]:
    """Strip the title line and the "Updated"/date/"Effective" metadata lines
    (which may appear anywhere in the first few lines, with no blank line
    separating the date from the body text that follows it)."""
    if not lines:
        return "", lines
    title = lines[0].strip()
    remaining = list(lines[1:])

    for i, line in enumerate(remaining[:10]):
        if line.strip() == "Updated":
            drop = {i}
            if i + 1 < len(remaining) and _DATE_LINE_RE.match(remaining[i + 1].strip()):
                drop.add(i + 1)
            j = i + 1
            while j < len(remaining) and remaining[j].strip().startswith(("Effective", "(Previous")):
                drop.add(j)
                j += 1
            remaining = [ln for k, ln in enumerate(remaining) if k not in drop]
            break

    return title, remaining


def parse_sections(text: str) -> list[dict]:
    """Break document text into section/clause units.

    Returns a list of {"path": [breadcrumb parts], "section_number": str|None,
    "clause_id": str|None, "text": str} dicts in document order.
    """
    raw_lines = [ln.strip() for ln in text.split("\n")]
    title, body_lines = _parse_header(raw_lines)

    paragraphs = []
    current: list[str] = []
    for line in body_lines:
        if line == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(" ".join(current))

    units: list[dict] = []
    section_title: str | None = None
    section_number: str | None = None

    for para in paragraphs:
        if _is_heading(para):
            section_title = para
            section_number = None
            continue

        m_num = _NUMBERED_SECTION_RE.match(para)
        m_letter = _LETTERED_CLAUSE_RE.match(para)

        if m_num:
            section_number, rest = m_num.group(1), m_num.group(2)
            section_title = None
            path = [title, f"{section_number}. {rest.split('.')[0][:60]}".rstrip()]
            units.append({"path": path, "section_number": section_number,
                           "clause_id": None, "text": para})
        elif m_letter and section_number:
            clause_id = f"{section_number}{m_letter.group(1)}"
            path = [title, f"Section {section_number}", f"({m_letter.group(1)})"]
            units.append({"path": path, "section_number": section_number,
                           "clause_id": clause_id, "text": para})
        else:
            path = [title] + ([section_title] if section_title else [])
            units.append({"path": path, "section_number": section_number,
                           "clause_id": None, "text": para})

    return _merge_undersized(units)


def _merge_undersized(units: list[dict], min_chars: int = MIN_CHUNK_CHARS) -> list[dict]:
    """Fold short fragments into the previous unit's text. If the fragment
    belongs to a different clause/section than the unit it's merged into,
    that identity is combined (not silently dropped), so the emitted
    breadcrumb/metadata still reflects everything the chunk actually contains."""
    merged: list[dict] = []
    for unit in units:
        if merged and len(unit["text"]) < min_chars:
            prev = merged[-1]
            prev["text"] += " " + unit["text"]

            if unit["clause_id"] and unit["clause_id"] != prev["clause_id"]:
                prev["clause_id"] = f"{prev['clause_id']}+{unit['clause_id']}" if prev["clause_id"] else unit["clause_id"]
            elif unit["section_number"] and unit["section_number"] != prev["section_number"]:
                prev["section_number"] = (f"{prev['section_number']}+{unit['section_number']}"
                                           if prev["section_number"] else unit["section_number"])

            for part in unit["path"]:
                if part and part not in prev["path"]:
                    prev["path"].append(part)
        else:
            merged.append(dict(unit))
    return merged


def chunk_document(text: str, source: str) -> list[tuple[str, dict]]:
    """Structure-aware chunking entrypoint.

    Returns a list of (chunk_text_with_breadcrumb, metadata) tuples, mirroring
    what ingestion.py needs to build ids/docs/metadatas for Chroma.
    """
    units = parse_sections(text)
    results: list[tuple[str, dict]] = []

    for unit in units:
        breadcrumb = " > ".join(p for p in unit["path"] if p)
        for piece in _split_oversized(unit["text"]):
            chunk = f"{breadcrumb}:\n{piece}" if breadcrumb else piece
            metadata = {
                "source": source,
                "doc_title": unit["path"][0] if unit["path"] else "",
                "section_number": unit["section_number"] or "",
                "clause_id": unit["clause_id"] or "",
            }
            results.append((chunk, metadata))

    return results
