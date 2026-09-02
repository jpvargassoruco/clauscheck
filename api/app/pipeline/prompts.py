"""Spanish LLM prompts (HLD §5). Kept compact — cost/latency matter.

`SYSTEM` states the fixed rules for every stage: Bolivia, cite only
provided article ids, JSON only. Each `*_prompt` builds the per-stage user
message from already-gathered context (never re-explains the whole task).
"""

SYSTEM = (
    "Eres un asistente jurídico especializado en derecho boliviano vigente. "
    "Respondes ÚNICAMENTE con un objeto JSON válido, sin texto adicional, "
    "explicaciones ni bloques de markdown. Cuando el contexto te proporcione "
    "artículos normativos identificados por un id, solo puedes citar esos "
    "ids exactos; nunca inventes artículos, números ni cites de memoria."
)


def clausulas_prompt(texto: str) -> str:
    return (
        "Separa el siguiente contrato en sus cláusulas. Para cada una da un "
        "id corto (c1, c2, ...), su número/nombre tal como aparece en el "
        "contrato (p.ej. 'PRIMERA'), un título breve y el texto literal "
        "completo de la cláusula.\n\n"
        f"Contrato:\n{texto}\n\n"
        'Responde: {"clausulas":[{"id":"c1","numero":"PRIMERA","titulo":"...","texto":"..."}]}'
    )


def partes_prompt(texto: str, clausulas: list[dict]) -> str:
    resumen = "\n".join(f"- {c['id']} ({c['numero']}): {c.get('titulo') or ''}" for c in clausulas)
    return (
        "Identifica las partes del contrato: id corto (p1, p2...), nombre o "
        "identificación tal como aparece, rol (p.ej. 'acreedor anticresista', "
        "'deudor anticresista', 'arrendador', 'trabajador'), y si redactó o "
        "propuso el contrato (redacto: true/false; normalmente solo una "
        "parte lo redactó). Extrae también la ficha del contrato cuando sea "
        "identificable: plaza, fecha, cuantía, forma_instrumental, "
        "tipo_contrato y rubro (uno de laboral|comercial|financiero|civil); "
        "usa null si no es identificable.\n\n"
        f"Contrato:\n{texto}\n\nCláusulas:\n{resumen}\n\n"
        'Responde: {"partes":[{"id":"p1","nombre":"...","rol":"...","redacto":true}],'
        '"ficha":{"plaza":null,"fecha":null,"cuantia":null,"forma_instrumental":null,'
        '"tipo_contrato":null,"rubro":null}}'
    )


def candidatos_prompt(clausulas: list[dict], partes: list[dict]) -> str:
    clausulas_txt = "\n".join(f"- {c['id']} ({c['numero']}): {c['texto']}" for c in clausulas)
    partes_txt = ", ".join(f"{p['id']}={p['nombre']} ({p['rol']})" for p in partes) or "(ninguna)"
    return (
        "Analiza cada cláusula y detecta patrones de riesgo: cláusulas "
        "abusivas, leoninas, ambiguas explotables, nulas/irrenunciables, o "
        "defectos técnicos menores. Detecta también OMISIONES: cláusulas "
        "que este tipo de contrato debería tener y no aparecen (p.ej. la "
        "restitución del capital en un anticrético). Para cada candidato da: "
        "id corto (h1, h2...), tipo ('hallazgo' o 'omision'), clausula_id "
        "(solo para 'hallazgo'; null en omisiones), titulo breve, problema "
        "(1-2 frases describiendo el riesgo jurídico, se usará para buscar "
        "normativa aplicable), nivel_tentativo "
        "(critico|alto|medio|bajo|informativo), palabras_clave (2-5 "
        "términos), y para 'hallazgo' además cita_textual (fragmento "
        "literal de la cláusula).\n\n"
        f"Partes: {partes_txt}\n\nCláusulas:\n{clausulas_txt}\n\n"
        'Responde: {"candidatos":[{"id":"h1","tipo":"hallazgo","clausula_id":"c1",'
        '"titulo":"...","problema":"...","nivel_tentativo":"alto",'
        '"palabras_clave":["..."],"cita_textual":"..."}]}'
    )


def contraste_prompt(
    candidatos: list[dict], retrieved: dict[str, list[dict]], partes: list[dict]
) -> str:
    partes_txt = ", ".join(f"{p['id']}={p['nombre']} ({p['rol']})" for p in partes) or "(ninguna)"
    bloques = []
    for cand in candidatos:
        arts = retrieved.get(cand["id"], [])
        if arts:
            arts_txt = "\n".join(
                "    * {id} [{cuerpo} {numero}{inciso}]: {texto}".format(
                    id=a["id"],
                    cuerpo=a["cuerpo"],
                    numero=a["numero"],
                    inciso=(" inc." + a["inciso"]) if a.get("inciso") else "",
                    texto=a["texto"],
                )
                for a in arts
            )
        else:
            arts_txt = "    (ninguno recuperado)"
        bloques.append(
            f"- {cand['id']} ({cand['tipo']}) problema: {cand['problema']}\n"
            f"  artículos candidatos:\n{arts_txt}"
        )
    return (
        "Para cada candidato decide si es un hallazgo/omisión real "
        "(applicable) y elige, ÚNICAMENTE entre los ids de artículo "
        "listados como candidatos de ESE ítem, los que efectivamente lo "
        "fundamentan (articulo_ids puede quedar vacío si ninguno aplica). "
        "Da el nivel final (critico|alto|medio|bajo|informativo). Para "
        "'hallazgo' indica qué parte se beneficia (beneficia) y cuál se "
        "perjudica (perjudica) usando los ids de partes, o null si no "
        "aplica claramente a una parte; da también fundamento (1-3 frases) "
        "y redaccion_sustitutiva (texto alternativo sugerido, o null). "
        "Para 'omision' da fundamento y recomendacion (texto, o null) en "
        "vez de redaccion_sustitutiva.\n\n"
        f"Partes: {partes_txt}\n\n" + "\n".join(bloques) + "\n\n"
        'Responde: {"resultados":[{"id":"h1","applicable":true,"nivel":"alto",'
        '"beneficia":"p2","perjudica":"p1","articulo_ids":["<id>"],'
        '"fundamento":"...","redaccion_sustitutiva":"...","recomendacion":null}]}'
    )


def dictamen_prompt(
    ficha: dict,
    partes: list[dict],
    hallazgos_ctx: list[dict],
    omisiones_ctx: list[dict],
    indice_riesgo: int,
    nivel: str,
) -> str:
    partes_txt = "\n".join(
        f"- {p['id']} {p['nombre']} ({p['rol']}), redacto={p.get('redacto', False)}, "
        f"balance calculado={p['balance']}, a_favor={p['a_favor']}, en_contra={p['en_contra']}"
        for p in partes
    )

    def _fmt_arts(arts: list[dict]) -> str:
        if not arts:
            return "(sin artículo aplicable)"
        return "; ".join(
            f"{a['articulo_id']} [{a['cuerpo']} {a['numero']}]: {a['texto']}" for a in arts
        )

    hallazgos_txt = (
        "\n".join(
            f"- {h['id']} nivel={h['nivel']} clausula={h.get('clausula_id')} "
            f"beneficia={h.get('beneficia')} perjudica={h.get('perjudica')} "
            f"titulo={h['titulo']!r} cita={h.get('cita_textual')!r} "
            f"fundamento_base={h['fundamento']!r} redaccion_base={h.get('redaccion_sustitutiva')!r} "
            f"articulos_disponibles=[{_fmt_arts(h['articulos'])}]"
            for h in hallazgos_ctx
        )
        or "(ninguno)"
    )
    omisiones_txt = (
        "\n".join(
            f"- {o['id']} nivel={o['nivel']} titulo={o['titulo']!r} "
            f"fundamento_base={o['fundamento']!r} recomendacion_base={o.get('recomendacion')!r} "
            f"articulos_disponibles=[{_fmt_arts(o['articulos'])}]"
            for o in omisiones_ctx
        )
        or "(ninguna)"
    )

    return (
        "Redacta el dictamen jurídico final en el formato JSON exacto "
        "indicado abajo (versión '1.0'). Usa EXACTAMENTE estos valores ya "
        "calculados de forma determinista, no los recalcules: "
        f"indice_riesgo={indice_riesgo}, nivel='{nivel}'; y para cada parte "
        "usa exactamente el balance/a_favor/en_contra ya calculado que se "
        "te da abajo. Tu trabajo es: escribir 'sintesis' (párrafo "
        "ejecutivo), 'lectura' de cada parte, pulir 'fundamento' y "
        "'redaccion_sustitutiva'/'recomendacion' a partir de las bases "
        "dadas, fijar 'confianza' (0..1) y proponer 'recomendaciones' "
        "priorizadas. En cada hallazgo/omisión, en 'articulos' cita "
        "ÚNICAMENTE ids de la lista 'articulos_disponibles' de ese ítem "
        "(puede quedar vacía); no agregues hallazgos/omisiones nuevos ni "
        "elimines los dados.\n\n"
        f"Ficha: {ficha}\n\nPartes:\n{partes_txt}\n\n"
        f"Hallazgos:\n{hallazgos_txt}\n\nOmisiones:\n{omisiones_txt}\n\n"
        "Responde con un objeto JSON con las claves: version, indice_riesgo, "
        "nivel, confianza, resumen ({hallazgos,omisiones,por_nivel}), "
        "sintesis, partes ([{id,nombre,rol,redacto,balance,a_favor,"
        "en_contra,lectura}]), hallazgos ([{id,nivel,titulo,clausula_id,"
        "cita_textual,fundamento,articulos:[{articulo_id,cuerpo,numero,"
        "inciso,texto,fuente_url}],redaccion_sustitutiva,beneficia,"
        "perjudica}]), omisiones ([{id,nivel,titulo,descripcion,articulos,"
        "recomendacion}]), recomendaciones ([{prioridad,tipo,accion}])."
    )
