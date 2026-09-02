"""Pydantic models for `documents.ficha/partes/clausulas` and `analyses.dictamen` (v1.0).

Must stay in sync with `web/src/types/dictamen.ts` (see docs/HLD.md §3).
"""

from enum import Enum

from pydantic import BaseModel, Field

DICTAMEN_VERSION = "1.0"


class Nivel(str, Enum):
    critico = "critico"
    alto = "alto"
    medio = "medio"
    bajo = "bajo"
    informativo = "informativo"


class RecomendacionTipo(str, Enum):
    correccion = "correccion"
    tramite = "tramite"
    asesoria = "asesoria"


# --- documents.ficha / partes / clausulas -----------------------------------


class Ficha(BaseModel):
    plaza: str | None = None
    fecha: str | None = None
    cuantia: str | None = None
    forma_instrumental: str | None = None
    tipo_contrato: str | None = None
    rubro: str | None = None


class ParteDocumento(BaseModel):
    id: str
    nombre: str
    rol: str
    redacto: bool = False


class Clausula(BaseModel):
    id: str
    numero: str
    titulo: str | None = None
    texto: str


# --- analyses.dictamen (v1.0) ------------------------------------------------


class ArticuloCitado(BaseModel):
    articulo_id: str
    cuerpo: str
    numero: str
    inciso: str | None = None
    texto: str
    fuente_url: str | None = None


class ResumenPorNivel(BaseModel):
    critico: int = 0
    alto: int = 0
    medio: int = 0
    bajo: int = 0
    informativo: int = 0


class Resumen(BaseModel):
    hallazgos: int = 0
    omisiones: int = 0
    por_nivel: ResumenPorNivel = Field(default_factory=ResumenPorNivel)


class ParteDictamen(BaseModel):
    id: str
    nombre: str
    rol: str
    redacto: bool = False
    balance: int = 0
    a_favor: int = 0
    en_contra: int = 0
    lectura: str | None = None


class Hallazgo(BaseModel):
    id: str
    nivel: Nivel
    titulo: str
    clausula_id: str | None = None
    cita_textual: str | None = None
    fundamento: str
    articulos: list[ArticuloCitado] = Field(default_factory=list)
    redaccion_sustitutiva: str | None = None
    beneficia: str | None = None
    perjudica: str | None = None


class Omision(BaseModel):
    id: str
    nivel: Nivel
    titulo: str
    descripcion: str
    articulos: list[ArticuloCitado] = Field(default_factory=list)
    recomendacion: str | None = None


class Recomendacion(BaseModel):
    prioridad: int
    tipo: RecomendacionTipo
    accion: str


class Dictamen(BaseModel):
    version: str = DICTAMEN_VERSION
    indice_riesgo: int = Field(ge=0, le=100)
    nivel: Nivel
    confianza: float = Field(ge=0, le=1)
    resumen: Resumen
    sintesis: str
    partes: list[ParteDictamen] = Field(default_factory=list)
    hallazgos: list[Hallazgo] = Field(default_factory=list)
    omisiones: list[Omision] = Field(default_factory=list)
    recomendaciones: list[Recomendacion] = Field(default_factory=list)


def dictamen_json_schema() -> dict:
    return Dictamen.model_json_schema()
