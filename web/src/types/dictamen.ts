/**
 * Espejo TypeScript del esquema JSON descrito en docs/HLD.md §3.
 * Debe coincidir exactamente con api/app/schemas/dictamen.py.
 */

export type Rubro = "laboral" | "comercial" | "financiero" | "civil";

export type Nivel = "critico" | "alto" | "medio" | "bajo" | "informativo";

export type RecomendacionTipo = "correccion" | "tramite" | "asesoria";

// ---- documents.ficha / partes / clausulas ----------------------------------

export interface Ficha {
  plaza: string;
  fecha: string;
  cuantia: string;
  forma_instrumental: string;
  tipo_contrato: string;
  rubro: Rubro;
}

export interface Parte {
  id: string;
  nombre: string;
  rol: string;
  redacto: boolean;
}

export interface Clausula {
  id: string;
  numero: string;
  titulo: string;
  texto: string;
}

export interface DocumentoContrato {
  id: string;
  titulo: string;
  tipo_contrato: string;
  rubro: Rubro;
  ficha: Ficha;
  partes: Parte[];
  clausulas: Clausula[];
  texto?: string;
  ocr_status?: "pending" | "ready" | "failed";
  is_public?: boolean;
  created_at?: string;
}

// ---- analyses.dictamen (version 1.0) ---------------------------------------

export interface ResumenPorNivel {
  critico: number;
  alto: number;
  medio: number;
  bajo: number;
  informativo: number;
}

export interface Resumen {
  hallazgos: number;
  omisiones: number;
  por_nivel: ResumenPorNivel;
}

export interface ParteDictamen {
  id: string;
  nombre: string;
  rol: string;
  redacto: boolean;
  balance: number; // -100..100
  a_favor: number;
  en_contra: number;
  lectura: string;
}

export interface ArticuloCitado {
  articulo_id: string;
  cuerpo: string;
  numero: string;
  inciso?: string | null;
  texto: string;
  fuente_url: string;
}

export interface Hallazgo {
  id: string;
  nivel: Nivel;
  titulo: string;
  clausula_id: string;
  cita_textual: string;
  fundamento: string;
  articulos: ArticuloCitado[];
  redaccion_sustitutiva: string;
  beneficia?: string | null;
  perjudica?: string | null;
}

export interface Omision {
  id: string;
  nivel: Nivel;
  titulo: string;
  descripcion: string;
  articulos: ArticuloCitado[];
  recomendacion: string;
}

export interface Recomendacion {
  prioridad: number;
  tipo: RecomendacionTipo;
  accion: string;
}

export interface Dictamen {
  version: "1.0";
  indice_riesgo: number; // 0..100
  nivel: Nivel;
  confianza: number; // 0..1
  resumen: Resumen;
  sintesis: string;
  partes: ParteDictamen[];
  hallazgos: Hallazgo[];
  omisiones: Omision[];
  recomendaciones: Recomendacion[];
}

// ---- niveles: orden y presentación -----------------------------------------

export const NIVEL_ORDEN: Nivel[] = [
  "critico",
  "alto",
  "medio",
  "bajo",
  "informativo"
];

export const NIVEL_LABEL: Record<Nivel, string> = {
  critico: "Crítico",
  alto: "Alto",
  medio: "Medio",
  bajo: "Bajo",
  informativo: "Informativo"
};

export const NIVEL_COLOR: Record<Nivel, string> = {
  critico: "#B3261E",
  alto: "#D97706",
  medio: "#C9A227",
  bajo: "#2563A8",
  informativo: "#1E7A4C"
};
