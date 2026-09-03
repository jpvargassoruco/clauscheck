"""Windowing helpers for long documents (pipeline stages 2 and 4).

Splits a long text/clause list into overlapping windows so a single LLM
call never has to process the full contract at once (context/output size
guards), then provides dedupe helpers so the per-window results recombine
into one coherent list — e.g. a 15.000-word contract still completes.
"""

WORD_WINDOW_SIZE = 3000
WORD_WINDOW_OVERLAP = 200


def split_words_with_overlap(
    texto: str, size: int = WORD_WINDOW_SIZE, overlap: int = WORD_WINDOW_OVERLAP
) -> list[str]:
    """Split `texto` into consecutive ~`size`-word windows sharing `overlap`
    words with the next one. Returns `[texto]` unchanged when it already
    fits in a single window."""
    palabras = texto.split()
    if len(palabras) <= size:
        return [texto]

    windows: list[str] = []
    start = 0
    n = len(palabras)
    while start < n:
        end = min(start + size, n)
        windows.append(" ".join(palabras[start:end]))
        if end >= n:
            break
        start = end - overlap
    return windows


def _clausula_key(c: dict) -> tuple[str, str]:
    return (
        str(c.get("numero", "")).strip().lower(),
        str(c.get("texto", "")).strip().lower()[:80],
    )


def dedupe_clausulas(clausulas: list[dict]) -> list[dict]:
    """Merge clause lists extracted from multiple windows, dropping
    duplicates the word-overlap between windows re-extracted (same
    `numero` and the same leading text)."""
    seen: set[tuple[str, str]] = set()
    result: list[dict] = []
    for c in clausulas:
        key = _clausula_key(c)
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
    return result


def chunk_clausulas(
    clausulas: list[dict], size: int = WORD_WINDOW_SIZE, overlap: int = WORD_WINDOW_OVERLAP
) -> list[list[dict]]:
    """Group clauses into chunks totalling ~`size` words, so stage 4
    (detectar patrones) processes a long contract's clauses in manageable
    batches. Consecutive chunks share trailing clauses (up to `overlap`
    words) for continuity of context across the boundary."""
    if not clausulas:
        return [[]]

    def word_count(c: dict) -> int:
        return len(str(c.get("texto", "")).split())

    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_words = 0
    for c in clausulas:
        w = word_count(c)
        if current and current_words + w > size:
            chunks.append(current)
            overlap_clauses: list[dict] = []
            overlap_words = 0
            for cc in reversed(current):
                cw = word_count(cc)
                if overlap_words + cw > overlap:
                    break
                overlap_clauses.insert(0, cc)
                overlap_words += cw
            current = list(overlap_clauses)
            current_words = overlap_words
        current.append(c)
        current_words += w
    if current:
        chunks.append(current)
    return chunks


def dedupe_candidatos(candidatos: list[dict]) -> list[dict]:
    """Drop duplicate hallazgos/omisiones re-detected on the same clause in
    the overlap between two stage-4 chunks (same tipo + clausula_id +
    titulo)."""
    seen: set[tuple] = set()
    result: list[dict] = []
    for c in candidatos:
        key = (
            c.get("tipo"),
            c.get("clausula_id"),
            str(c.get("titulo", "")).strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
    return result
