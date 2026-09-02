import styles from "../Landing.module.css";

const etapas = [
  { titulo: "Normaliza el texto", texto: "Limpia y estructura el texto del documento, ya sea cargado como texto o resultado del OCR." },
  { titulo: "Separa las cláusulas", texto: "Identifica cada cláusula del contrato y la numera de forma independiente." },
  { titulo: "Identifica a las partes", texto: "Reconoce a los intervinientes y determina quién redactó el clausulado." },
  { titulo: "Detecta patrones de riesgo", texto: "Señala, cláusula por cláusula, candidatos a abuso, ambigüedad u omisión." },
  { titulo: "Contrasta contra la norma", texto: "Busca los artículos aplicables del Código Civil, la CPE y la normativa laboral, y descarta citas que no existen en la base verificada." },
  { titulo: "Pondera el impacto por parte", texto: "Calcula de forma determinista el balance de cada parte y el índice de riesgo del contrato." },
  { titulo: "Redacta el dictamen", texto: "Produce el informe final: síntesis, reparto de cargas, hallazgos, omisiones y recomendaciones." }
];

export function ComoFunciona() {
  return (
    <section id="como-funciona" className={styles.seccion}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>Cómo funciona</span>
        <h2 className={styles.seccionTitulo}>
          El motor recorre siete etapas visibles
        </h2>
        <p className={styles.seccionIntro}>
          El recorrido completo, desde que se sube el contrato hasta que se
          tiene el dictamen en la mano, toma minutos y puede seguirse en
          tiempo real.
        </p>
        <ol className={styles.etapas}>
          {etapas.map((e, i) => (
            <li key={e.titulo} className={styles.etapa}>
              <span className={styles.etapaNumero}>{i + 1}</span>
              <div className={styles.etapaTexto}>
                <h3>{e.titulo}</h3>
                <p>{e.texto}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
