import { Link } from "react-router-dom";
import styles from "../Landing.module.css";

export function Hero() {
  return (
    <section className={styles.hero}>
      <div className={`${styles.heroGrid} contenedor`}>
        <div>
          <h1 className={styles.heroTitulo}>
            Antes de firmar, sepa a quién favorece cada cláusula.
          </h1>
          <p className={styles.heroSubtitulo}>
            ClausCheck revisa un contrato cláusula por cláusula, señala
            cuáles están mal redactadas o desequilibradas, y dice con
            nombre y apellido a qué parte benefician y a cuál perjudican,
            citando la norma boliviana que lo sostiene.
          </p>
          <div className={styles.heroAcciones}>
            <Link to="/solicitar-acceso" className="boton boton-primario">
              Solicitar acceso
            </Link>
            <a href="#ejemplos" className="boton boton-secundario">
              Ver ejemplos
            </a>
          </div>
        </div>

        <div className={`${styles.heroPanel} tarjeta`}>
          <div className={styles.heroPanelFila}>
            <span className={styles.heroPanelEtiqueta}>Índice de riesgo</span>
            <strong>87 / 100 — Crítico</strong>
          </div>
          <div className={styles.heroPanelFila}>
            <span className={styles.heroPanelEtiqueta}>Contrastado contra</span>
            <strong>Código Civil, CPE, normativa laboral</strong>
          </div>
          <div className={styles.heroPanelFila}>
            <span className={styles.heroPanelEtiqueta}>Cada cita</span>
            <strong>Texto oficial verificado, con fuente</strong>
          </div>
          <div className={styles.heroPanelFila}>
            <span className={styles.heroPanelEtiqueta}>Tiempo de análisis</span>
            <strong>7 etapas, minutos</strong>
          </div>
        </div>
      </div>
    </section>
  );
}
