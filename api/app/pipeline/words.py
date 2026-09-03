"""Word counting, shared by the documents/analyses routers and the pipeline.

A simple whitespace split is good enough for the plan-enforcement use case
(consistent counting everywhere matters more than linguistic precision).
"""


def contar_palabras(texto: str | None) -> int:
    if not texto:
        return 0
    return len(texto.split())
