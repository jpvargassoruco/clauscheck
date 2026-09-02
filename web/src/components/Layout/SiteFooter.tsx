import { Link } from "react-router-dom";
import styles from "./Layout.module.css";

export function SiteFooter() {
  return (
    <footer className={styles.siteFooter}>
      <div className={`${styles.siteFooterInner} contenedor`}>
        <div>
          <div className={styles.marca}>
            <span className={styles.marcaClaus}>Claus</span>
            <span className={styles.marcaCheck}>Check</span>
          </div>
          <p className={styles.footerTagline}>
            Detección de cláusulas abusivas en contratos, con dictamen
            respaldado en normativa boliviana.
          </p>
        </div>
        <nav className={styles.footerNav} aria-label="Enlaces del pie">
          <Link to="/manual">Manual</Link>
          <a href="/#planes">Planes</a>
          <a href="/#equipo">Equipo</a>
          <a href="/#contacto">Contacto</a>
          <Link to="/login">Iniciar sesión</Link>
        </nav>
        <p className={styles.disclaimer}>
          ClausCheck es una herramienta de apoyo a la revisión contractual y
          no sustituye a un abogado. Las citas normativas se contrastan
          contra la base de datos verificada, pero la decisión sobre un
          contrato concreto corresponde siempre a un profesional del
          derecho habilitado.
        </p>
        <p className={styles.copy}>
          © {new Date().getFullYear()} ClausCheck LegalTech · UAGRM · Santa
          Cruz de la Sierra, Bolivia
        </p>
      </div>
    </footer>
  );
}
