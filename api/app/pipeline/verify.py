"""Stage 7 post-processing — verificador (HLD §5).

Every `articulos[].articulo_id` in the LLM-authored dictamen must both exist
in the DB and be among the ids actually retrieved for this analysis (an id
the model could see at some point during stage 5) — never a citation
invented from memory. Valid citations get their display fields
(`texto`/`fuente_url`/`cuerpo`/`numero`/`inciso`) overwritten with the DB
row, since the officially shown normative text is always the DB's, never
the model's paraphrase. Invalid citations are dropped and `confianza` is
lowered by `CONFIANZA_PENALTY` per drop, floored at `CONFIANZA_FLOOR`.
"""

CONFIANZA_PENALTY = 0.1
CONFIANZA_FLOOR = 0.2


def verify_citations(
    dictamen: dict, allowed_ids: set[str], articulos_by_id: dict[str, dict]
) -> dict:
    dropped = 0

    def _fix_list(items: list[dict]) -> None:
        nonlocal dropped
        for item in items:
            kept: list[dict] = []
            for cita in item.get("articulos") or []:
                aid = str(cita.get("articulo_id", ""))
                art = articulos_by_id.get(aid)
                if aid not in allowed_ids or art is None:
                    dropped += 1
                    continue
                cita["articulo_id"] = aid
                cita["cuerpo"] = art["cuerpo"]
                cita["numero"] = art["numero"]
                cita["inciso"] = art["inciso"]
                cita["texto"] = art["texto"]
                cita["fuente_url"] = art["fuente_url"]
                kept.append(cita)
            item["articulos"] = kept

    _fix_list(dictamen.get("hallazgos") or [])
    _fix_list(dictamen.get("omisiones") or [])

    if dropped:
        confianza = float(dictamen.get("confianza", 0.5)) - CONFIANZA_PENALTY * dropped
        dictamen["confianza"] = max(CONFIANZA_FLOOR, round(confianza, 2))

    return dictamen
