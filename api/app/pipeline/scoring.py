"""Stage 6 — ponderar: deterministic per-parte balance and overall risk index.

No LLM call — pure function of the finalized hallazgos (stage 5 output:
each with `nivel`, `beneficia`, `perjudica`). Omisiones do not enter the
formula (HLD §3 only weighs hallazgos against parte balances); they still
count toward `resumen.omisiones`.

Weights per nivel (HLD §3 escala critico > alto > medio > bajo > informativo):

    critico=40  alto=25  medio=12  bajo=5  informativo=0

Balance por parte (saturado en [-100, 100]): suma de los pesos de los
hallazgos que la benefician, menos la suma de los pesos de los que la
perjudican.

Índice de riesgo (0..100): sea `pesos` la lista de pesos de todos los
hallazgos, `max_w` el mayor y `resto` la suma de los demás:

    indice = min(100, round(max_w * 2.5 + resto * 0.3))

El peso mayor pesa 2.5x (domina el índice) y el resto pesa 0.3x cada uno
(agrava pero no domina). Un único hallazgo crítico aislado (peso 40) ya
produce 40 * 2.5 = 100, cumpliendo el requisito de que un crítico por sí
solo dispare el índice a un nivel alto (>=85); varios hallazgos menores se
acumulan pero nunca superan a un crítico aislado salvo que también existan
otros hallazgos fuertes.

Nivel global (HLD `nivel`) se deriva del índice ya calculado:

    >=85 critico  >=60 alto  >=35 medio  >=15 bajo  <15 informativo
"""

NIVEL_WEIGHT: dict[str, int] = {
    "critico": 40,
    "alto": 25,
    "medio": 12,
    "bajo": 5,
    "informativo": 0,
}


def nivel_from_indice(indice: int) -> str:
    if indice >= 85:
        return "critico"
    if indice >= 60:
        return "alto"
    if indice >= 35:
        return "medio"
    if indice >= 15:
        return "bajo"
    return "informativo"


def ponderar(
    hallazgos: list[dict], parte_ids: list[str]
) -> tuple[dict[str, dict[str, int]], int, str]:
    """Compute per-parte balance/a_favor/en_contra and the global indice/nivel.

    `hallazgos` items need `nivel` (str), `beneficia` (parte id or None) and
    `perjudica` (parte id or None). `parte_ids` are the known parte ids (any
    beneficia/perjudica id not in this list is ignored). Returns
    `(partes_calc, indice_riesgo, nivel)` where `partes_calc` maps
    `parte_id -> {"balance": int, "a_favor": int, "en_contra": int}`.
    """
    partes_calc: dict[str, dict[str, int]] = {
        pid: {"balance": 0, "a_favor": 0, "en_contra": 0} for pid in parte_ids
    }
    weights: list[int] = []

    for h in hallazgos:
        weight = NIVEL_WEIGHT.get(h.get("nivel"), 0)
        weights.append(weight)
        beneficia = h.get("beneficia")
        perjudica = h.get("perjudica")
        if beneficia in partes_calc:
            partes_calc[beneficia]["balance"] += weight
            partes_calc[beneficia]["a_favor"] += 1
        if perjudica in partes_calc:
            partes_calc[perjudica]["balance"] -= weight
            partes_calc[perjudica]["en_contra"] += 1

    for calc in partes_calc.values():
        calc["balance"] = max(-100, min(100, calc["balance"]))

    if weights:
        max_w = max(weights)
        resto = sum(weights) - max_w
        indice = min(100, round(max_w * 2.5 + resto * 0.3))
    else:
        indice = 0

    return partes_calc, indice, nivel_from_indice(indice)
