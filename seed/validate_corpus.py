#!/usr/bin/env python3
"""Valida `seed/corpus/*.json` contra `seed/normativa.json` y el esquema
Pydantic de `api/app/schemas/dictamen.py` (docs/HLD.md §3 y §7).

Uso:
    PYTHONPATH=api python3 seed/validate_corpus.py

Si `pydantic` no está disponible en el intérprete activo, usar el venv de
la API (ya trae pydantic instalado) o crear uno en /tmp:
    api/.venv/bin/python3 -m pip install --user pydantic   # si hiciera falta
    PYTHONPATH=api api/.venv/bin/python3 seed/validate_corpus.py

Comprueba, para cada documento del corpus:
  1. `document` valida contra el modelo de ficha/partes/clausulas.
  2. `dictamen` valida contra el JSON Schema producido por
     `dictamen_json_schema()` y contra el modelo `Dictamen` (más estricto:
     valida enums de `nivel`/`tipo`).
  3. Toda cita en `hallazgos[].articulos` / `omisiones[].articulos` resuelve
     a una entrada real de `seed/normativa.json` (cuerpo + numero + inciso).
  4. Todo `cita_textual` es substring literal del texto de su
     `clausula_id` en `document.clausulas`.
  5. `dictamen.resumen` (hallazgos, omisiones, por_nivel) coincide con el
     conteo real de `dictamen.hallazgos` / `dictamen.omisiones`.
  6. `indice_riesgo`, `nivel` y `resumen.hallazgos` coinciden con la tabla
     del Manual §05 (hardcodeada abajo).

Sale con código != 0 si algo falla, e imprime un resumen por documento.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_DIR = REPO_ROOT / "seed"
CORPUS_DIR = SEED_DIR / "corpus"
NORMATIVA_PATH = SEED_DIR / "normativa.json"

# Añadir api/ al path para poder hacer `from app.schemas.dictamen import ...`
# igual que si se hubiese exportado PYTHONPATH=api.
API_DIR = REPO_ROOT / "api"
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover - se reporta como error de entorno
    jsonschema = None

try:
    from pydantic import ValidationError

    from app.schemas.dictamen import (  # type: ignore
        Clausula,
        Dictamen,
        Ficha,
        ParteDocumento,
        dictamen_json_schema,
    )
except ImportError as exc:  # pragma: no cover
    print(
        "ERROR: no se pudo importar pydantic / app.schemas.dictamen.\n"
        f"  detalle: {exc}\n"
        "Ejecutar con: PYTHONPATH=api api/.venv/bin/python3 seed/validate_corpus.py\n"
        "o instalar pydantic en el intérprete activo "
        "(pip install --user pydantic) / usar un venv en /tmp.",
        file=sys.stderr,
    )
    sys.exit(2)


# Tabla del Manual de ClausCheck §05 "Los contratos incluidos"
# (índice de riesgo, nivel, nº de hallazgos), en el orden de la tabla.
MANUAL_TABLA = {
    "01": (100, "critico", 8),   # Prestación de servicios inmobiliarios con exclusividad
    "02": (100, "critico", 7),   # Préstamo de dinero con garantía hipotecaria
    "03": (98, "critico", 6),    # Minuta de compraventa de bien inmueble
    "04": (95, "critico", 7),    # Contrato de trabajo indefinido — Regente bioquímica
    "05": (87, "critico", 5),    # Contrato de anticrético sobre tienda comercial
    "06": (80, "critico", 6),    # Contrato privado de arrendamiento de vivienda
    "07": (75, "alto", 5),       # Contrato de tolerado sobre salón con baño privado
    "08": (75, "alto", 5),       # Transferencia de motocicleta scooter
    "09": (67, "alto", 6),       # Contrato de trabajo indefinido — Regente farmacéutica
    "10": (49, "medio", 4),      # Documento de cancelación de dinero entre copropietarios
    "11": (41, "medio", 4),      # Contrato privado de exclusividad para venta de inmueble
}


class ValidationFailure(Exception):
    pass


def load_normativa() -> set[tuple[str, str, str | None]]:
    data = json.loads(NORMATIVA_PATH.read_text(encoding="utf-8"))
    claves: set[tuple[str, str, str | None]] = set()
    for a in data["articulos"]:
        claves.add((a["cuerpo"], a["numero"], a.get("inciso")))
    return claves


def doc_id_from_filename(name: str) -> str:
    # "01-servicios-inmobiliarios-exclusividad.json" -> "01"
    return name.split("-", 1)[0]


def check_articulos(prefix: str, articulos: list[dict], normativa_claves: set) -> list[str]:
    errores = []
    for a in articulos:
        clave = (a["cuerpo"], a["numero"], a.get("inciso"))
        if clave not in normativa_claves:
            errores.append(f"{prefix}: cita inexistente en normativa.json: {clave}")
    return errores


def check_resumen(dictamen: dict) -> list[str]:
    errores = []
    resumen = dictamen["resumen"]
    hallazgos = dictamen["hallazgos"]
    omisiones = dictamen["omisiones"]

    if resumen["hallazgos"] != len(hallazgos):
        errores.append(
            f"resumen.hallazgos ({resumen['hallazgos']}) != len(hallazgos) ({len(hallazgos)})"
        )
    if resumen["omisiones"] != len(omisiones):
        errores.append(
            f"resumen.omisiones ({resumen['omisiones']}) != len(omisiones) ({len(omisiones)})"
        )

    por_nivel_calc = {"critico": 0, "alto": 0, "medio": 0, "bajo": 0, "informativo": 0}
    for h in hallazgos:
        por_nivel_calc[h["nivel"]] += 1
    por_nivel_decl = resumen["por_nivel"]
    for nivel, count in por_nivel_calc.items():
        if por_nivel_decl.get(nivel, 0) != count:
            errores.append(
                f"resumen.por_nivel.{nivel} ({por_nivel_decl.get(nivel, 0)}) != real ({count})"
            )
    return errores


def check_citas(document: dict, dictamen: dict) -> list[str]:
    errores = []
    clausulas_por_id = {c["id"]: c["texto"] for c in document["clausulas"]}
    for h in dictamen["hallazgos"]:
        cita = h.get("cita_textual")
        if cita is None:
            continue
        clausula_id = h.get("clausula_id")
        texto_c = clausulas_por_id.get(clausula_id)
        if texto_c is None:
            errores.append(f"hallazgo {h['id']}: clausula_id {clausula_id!r} no existe en document.clausulas")
            continue
        if cita not in texto_c:
            errores.append(f"hallazgo {h['id']}: cita_textual no es substring literal de la cláusula {clausula_id}")
    return errores


def check_manual_tabla(doc_id: str, dictamen: dict) -> list[str]:
    errores = []
    if doc_id not in MANUAL_TABLA:
        errores.append(f"doc_id {doc_id!r} no está en la tabla del Manual §05")
        return errores
    idx, nivel, nhallazgos = MANUAL_TABLA[doc_id]
    if dictamen["indice_riesgo"] != idx:
        errores.append(f"indice_riesgo {dictamen['indice_riesgo']} != Manual {idx}")
    if dictamen["nivel"] != nivel:
        errores.append(f"nivel {dictamen['nivel']!r} != Manual {nivel!r}")
    if dictamen["resumen"]["hallazgos"] != nhallazgos:
        errores.append(f"resumen.hallazgos {dictamen['resumen']['hallazgos']} != Manual {nhallazgos}")
    return errores


def check_document_schema(document: dict) -> list[str]:
    errores = []
    try:
        Ficha.model_validate(document["ficha"])
    except ValidationError as exc:
        errores.append(f"document.ficha inválida: {exc}")
    for p in document["partes"]:
        try:
            ParteDocumento.model_validate(p)
        except ValidationError as exc:
            errores.append(f"document.partes[{p.get('id')}] inválida: {exc}")
    for c in document["clausulas"]:
        try:
            Clausula.model_validate(c)
        except ValidationError as exc:
            errores.append(f"document.clausulas[{c.get('id')}] inválida: {exc}")
    for campo in ("titulo", "tipo_contrato", "rubro", "ficha", "partes", "clausulas", "texto", "is_public"):
        if campo not in document:
            errores.append(f"document: falta el campo {campo!r}")
    if document.get("is_public") is not True:
        errores.append("document.is_public debe ser true en el corpus demo")
    return errores


def check_dictamen_schema(dictamen: dict) -> list[str]:
    errores = []
    # (a) validación estricta con el modelo pydantic (enums, tipos, requeridos)
    try:
        Dictamen.model_validate(dictamen)
    except ValidationError as exc:
        errores.append(f"dictamen no valida contra el modelo Dictamen: {exc}")
        return errores  # sin más sentido seguir si ni siquiera parsea

    # (b) validación adicional contra el JSON Schema generado por el propio
    #     módulo, tal como pide el encargo.
    if jsonschema is not None:
        schema = dictamen_json_schema()
        try:
            jsonschema.validate(instance=dictamen, schema=schema)
        except jsonschema.exceptions.ValidationError as exc:  # type: ignore[attr-defined]
            errores.append(f"dictamen no valida contra dictamen_json_schema(): {exc.message}")
    else:
        errores.append("AVISO: paquete 'jsonschema' no disponible; se omitió la validación de JSON Schema cruda")
    return errores


def validate_file(path: Path, normativa_claves: set) -> list[str]:
    errores: list[str] = []
    payload = json.loads(path.read_text(encoding="utf-8"))

    for campo in ("nota", "document", "dictamen"):
        if campo not in payload:
            errores.append(f"falta el campo de nivel superior {campo!r}")
    if errores:
        return errores

    if "sintético" not in payload["nota"] and "sintetico" not in payload["nota"]:
        errores.append("el campo 'nota' no parece advertir que el contenido es sintético")

    document = payload["document"]
    dictamen = payload["dictamen"]
    doc_id = doc_id_from_filename(path.name)

    errores += check_document_schema(document)
    errores += check_dictamen_schema(dictamen)
    errores += check_articulos("hallazgos", [a for h in dictamen["hallazgos"] for a in h["articulos"]], normativa_claves)
    errores += check_articulos("omisiones", [a for o in dictamen["omisiones"] for a in o["articulos"]], normativa_claves)
    errores += check_citas(document, dictamen)
    errores += check_resumen(dictamen)
    errores += check_manual_tabla(doc_id, dictamen)

    return errores


def main() -> int:
    if not NORMATIVA_PATH.exists():
        print(f"ERROR: no existe {NORMATIVA_PATH}", file=sys.stderr)
        return 2
    if not CORPUS_DIR.exists():
        print(f"ERROR: no existe {CORPUS_DIR}", file=sys.stderr)
        return 2

    normativa_claves = load_normativa()
    archivos = sorted(CORPUS_DIR.glob("*.json"))
    if not archivos:
        print(f"ERROR: no se encontraron archivos .json en {CORPUS_DIR}", file=sys.stderr)
        return 2

    total_errores = 0
    ids_encontrados = set()
    for path in archivos:
        errores = validate_file(path, normativa_claves)
        ids_encontrados.add(doc_id_from_filename(path.name))
        estado = "OK" if not errores else f"FALLÓ ({len(errores)} error(es))"
        print(f"[{estado}] {path.name}")
        for e in errores:
            print(f"    - {e}")
        total_errores += len(errores)

    faltantes = set(MANUAL_TABLA) - ids_encontrados
    if faltantes:
        print(f"[FALLÓ] faltan documentos del Manual §05: {sorted(faltantes)}")
        total_errores += len(faltantes)

    print()
    if total_errores:
        print(f"RESULTADO: {total_errores} error(es) en {len(archivos)} archivo(s).")
        return 1

    print(f"RESULTADO: OK — {len(archivos)} archivos del corpus validados sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
