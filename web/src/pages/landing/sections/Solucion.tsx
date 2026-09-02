import styles from "../Landing.module.css";

const partesDictamen = [
  {
    numero: "01",
    titulo: "Índice de riesgo",
    texto:
      "Un número de 0 a 100 que resume el estado del contrato completo, con el recuento de hallazgos, omisiones y el grado de confianza del motor. No es un promedio: un solo hallazgo crítico eleva el índice."
  },
  {
    numero: "02",
    titulo: "Síntesis ejecutiva",
    texto:
      "Un párrafo que dice qué es este contrato y cuál es su problema principal, escrito para que alguien que no leyó el documento entienda la situación."
  },
  {
    numero: "03",
    titulo: "Reparto de cargas",
    texto:
      "La respuesta directa a la pregunta que motiva la revisión: a quién beneficia el contrato. Cada parte recibe un balance de −100 a +100 y una lectura de su posición real."
  },
  {
    numero: "04",
    titulo: "Hallazgos",
    texto:
      "El cuerpo del informe, ordenado por gravedad. Cada hallazgo cita el fragmento textual del contrato, explica el fundamento jurídico, reproduce el artículo aplicable y propone una redacción sustitutiva."
  },
  {
    numero: "05",
    titulo: "Omisiones",
    texto:
      "Los puntos que este tipo de contrato debía regular y que el instrumento no contempla. En varios casos es la sección más grave del dictamen."
  },
  {
    numero: "06",
    titulo: "Recomendaciones",
    texto:
      "Qué hacer, en orden de prioridad: desde corregir una cláusula hasta trámites concretos, como protocolizar una minuta o inscribir una garantía en Derechos Reales."
  }
];

export function Solucion() {
  return (
    <section id="producto" className={`${styles.seccion} ${styles.seccionAlterna}`}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>La solución</span>
        <h2 className={styles.seccionTitulo}>
          ClausCheck toma un contrato, lo separa en cláusulas y lo contrasta
          contra la norma
        </h2>
        <p className={styles.seccionIntro}>
          ClausCheck existe para adelantar el descubrimiento de esos
          defectos. Toma un contrato, lo separa en cláusulas y contrasta cada
          una contra el Código Civil, la Constitución Política del Estado y
          la normativa laboral vigente de Bolivia. Devuelve un dictamen
          escrito en el lenguaje de un informe legal, no en el de una
          aplicación, que se lee de arriba abajo y va de lo general a lo
          particular.
        </p>
        <div className={styles.solucionGrid}>
          {partesDictamen.map((p) => (
            <div key={p.numero} className={`${styles.solucionTarjeta} tarjeta`}>
              <span className={styles.solucionNumero}>{p.numero}</span>
              <h3>{p.titulo}</h3>
              <p>{p.texto}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
