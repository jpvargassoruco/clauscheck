import { NIVEL_LABEL, NIVEL_ORDEN, type Dictamen } from "@/types/dictamen";

/** Serializa el informe completo a texto plano, para "Copiar informe completo". */
export function dictamenATexto(d: Dictamen, tituloDocumento?: string): string {
  const lineas: string[] = [];
  const sep = "—".repeat(48);

  lineas.push("INFORME DE REVISIÓN ASISTIDA — CLAUSCHECK");
  if (tituloDocumento) lineas.push(tituloDocumento);
  lineas.push(sep);
  lineas.push(
    "Este informe es una herramienta de apoyo a la revisión contractual generada por software. No constituye asesoramiento legal ni sustituye el criterio de un abogado habilitado. Las citas normativas reproducen el texto oficial; su aplicación a un caso concreto requiere revisión profesional."
  );
  lineas.push(sep);
  lineas.push(
    `Índice de riesgo: ${d.indice_riesgo}/100 — Nivel: ${NIVEL_LABEL[d.nivel]}`
  );
  lineas.push(`Confianza del motor: ${Math.round(d.confianza * 100)}%`);
  lineas.push(
    `Hallazgos: ${d.resumen.hallazgos} · Omisiones: ${d.resumen.omisiones}`
  );
  lineas.push(
    `Por nivel — crítico: ${d.resumen.por_nivel.critico}, alto: ${d.resumen.por_nivel.alto}, medio: ${d.resumen.por_nivel.medio}, bajo: ${d.resumen.por_nivel.bajo}, informativo: ${d.resumen.por_nivel.informativo}`
  );
  lineas.push("");

  lineas.push("SÍNTESIS EJECUTIVA");
  lineas.push(d.sintesis);
  lineas.push("");

  lineas.push("REPARTO DE CARGAS");
  for (const p of d.partes) {
    lineas.push(
      `${p.nombre} (${p.rol})${p.redacto ? " — redactó el clausulado" : ""}: balance ${p.balance > 0 ? "+" : ""}${p.balance}, ${p.a_favor} a favor / ${p.en_contra} en contra`
    );
    lineas.push(`  ${p.lectura}`);
  }
  lineas.push("");

  lineas.push("HALLAZGOS");
  const hallazgosOrdenados = [...d.hallazgos].sort(
    (a, b) => NIVEL_ORDEN.indexOf(a.nivel) - NIVEL_ORDEN.indexOf(b.nivel)
  );
  for (const h of hallazgosOrdenados) {
    lineas.push(`[${NIVEL_LABEL[h.nivel]}] ${h.titulo} (cláusula ${h.clausula_id})`);
    lineas.push(`  Cita: "${h.cita_textual}"`);
    lineas.push(`  Fundamento: ${h.fundamento}`);
    for (const a of h.articulos) {
      lineas.push(
        `  Art. ${a.numero}${a.inciso ? `.${a.inciso}` : ""} ${a.cuerpo}: ${a.texto} (${a.fuente_url})`
      );
    }
    lineas.push(`  Redacción sustitutiva: ${h.redaccion_sustitutiva}`);
    lineas.push("");
  }

  lineas.push("OMISIONES");
  const omisionesOrdenadas = [...d.omisiones].sort(
    (a, b) => NIVEL_ORDEN.indexOf(a.nivel) - NIVEL_ORDEN.indexOf(b.nivel)
  );
  for (const o of omisionesOrdenadas) {
    lineas.push(`[${NIVEL_LABEL[o.nivel]}] ${o.titulo}`);
    lineas.push(`  ${o.descripcion}`);
    for (const a of o.articulos) {
      lineas.push(
        `  Art. ${a.numero}${a.inciso ? `.${a.inciso}` : ""} ${a.cuerpo}: ${a.texto} (${a.fuente_url})`
      );
    }
    lineas.push(`  Recomendación: ${o.recomendacion}`);
    lineas.push("");
  }

  lineas.push("RECOMENDACIONES");
  const recsOrdenadas = [...d.recomendaciones].sort(
    (a, b) => a.prioridad - b.prioridad
  );
  for (const r of recsOrdenadas) {
    lineas.push(`${r.prioridad}. [${r.tipo}] ${r.accion}`);
  }
  lineas.push("");
  lineas.push(sep);
  lineas.push(
    "ClausCheck es una herramienta de apoyo a la revisión contractual, no sustituye a un abogado."
  );

  return lineas.join("\n");
}
