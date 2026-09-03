"""Unit tests for the pipeline's long-document windowing helpers
(`app.pipeline.windows`), used by stages 2 and 4 to let a long contract
complete despite max_tokens guards (see prompt item 3)."""

from app.pipeline.windows import (
    chunk_clausulas,
    dedupe_candidatos,
    dedupe_clausulas,
    split_words_with_overlap,
)


def test_split_words_with_overlap_short_text_stays_single_window():
    texto = " ".join(f"w{i}" for i in range(100))
    windows = split_words_with_overlap(texto, size=3000, overlap=200)
    assert windows == [texto]


def test_split_words_with_overlap_long_text_splits_with_overlap():
    palabras = [f"w{i}" for i in range(7000)]
    texto = " ".join(palabras)
    windows = split_words_with_overlap(texto, size=3000, overlap=200)

    assert len(windows) == 3  # 0-3000, 2800-5800, 5600-7000
    for w in windows:
        assert len(w.split()) <= 3000
    # consecutive windows share the overlap words
    assert windows[0].split()[-200:] == windows[1].split()[:200]
    # every original word is covered by some window
    covered = set()
    for w in windows:
        covered.update(w.split())
    assert covered == set(palabras)


def test_dedupe_clausulas_drops_reextracted_overlap_duplicates():
    clausulas = [
        {"id": "c1", "numero": "PRIMERA", "texto": "El objeto del contrato es..."},
        {"id": "c2", "numero": "SEGUNDA", "texto": "El precio pactado es..."},
        # re-extracted from the next window's overlap: same numero/prefix
        {"id": "c1", "numero": "PRIMERA", "texto": "El objeto del contrato es..."},
        {"id": "c3", "numero": "TERCERA", "texto": "El plazo del contrato es..."},
    ]
    result = dedupe_clausulas(clausulas)
    assert [c["numero"] for c in result] == ["PRIMERA", "SEGUNDA", "TERCERA"]


def test_chunk_clausulas_groups_by_word_budget_with_overlap():
    clausulas = [
        {"id": f"c{i}", "numero": str(i), "texto": " ".join(["palabra"] * 1000)} for i in range(1, 5)
    ]
    chunks = chunk_clausulas(clausulas, size=3000, overlap=200)
    assert len(chunks) == 2
    assert [c["id"] for c in chunks[0]] == ["c1", "c2", "c3"]
    # c3 (1000 words) is under the 200-word overlap budget only partially;
    # the overlap carries whatever trailing clauses fit within 200 words —
    # here none do, so the second chunk starts fresh with c4.
    assert [c["id"] for c in chunks[1]] == ["c4"]


def test_chunk_clausulas_empty_returns_single_empty_chunk():
    assert chunk_clausulas([]) == [[]]


def test_dedupe_candidatos_drops_same_clause_titulo_duplicates():
    candidatos = [
        {"id": "w0_h1", "tipo": "hallazgo", "clausula_id": "c2", "titulo": "Interés usurario"},
        {"id": "w1_h1", "tipo": "hallazgo", "clausula_id": "c2", "titulo": "Interés usurario"},
        {"id": "w1_o1", "tipo": "omision", "clausula_id": None, "titulo": "Falta restitución"},
    ]
    result = dedupe_candidatos(candidatos)
    assert len(result) == 2
    assert result[0]["id"] == "w0_h1"
    assert result[1]["id"] == "w1_o1"
