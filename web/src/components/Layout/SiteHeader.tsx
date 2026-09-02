import { Link, NavLink } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import { ThemeToggle } from "./ThemeToggle";
import styles from "./Layout.module.css";

const enlaces = [
  { href: "/#producto", label: "Producto" },
  { href: "/#ejemplos", label: "Ejemplos" },
  { href: "/#planes", label: "Planes" },
  { href: "/manual", label: "Manual" },
  { href: "/#contacto", label: "Contacto" }
];

export function SiteHeader() {
  const user = useAuthStore((s) => s.user);

  return (
    <header className={styles.siteHeader}>
      <div className={`${styles.siteHeaderInner} contenedor`}>
        <Link to="/" className={styles.marca}>
          <span className={styles.marcaClaus}>Claus</span>
          <span className={styles.marcaCheck}>Check</span>
        </Link>
        <nav className={styles.nav} aria-label="Navegación principal">
          {enlaces.map((e) => (
            <a key={e.href} href={e.href}>
              {e.label}
            </a>
          ))}
        </nav>
        <div className={styles.accionesHeader}>
          <ThemeToggle />
          {user ? (
            <NavLink to="/app" className="boton boton-primario">
              Ir a la app
            </NavLink>
          ) : (
            <>
              <Link to="/login" className="boton boton-secundario">
                Iniciar sesión
              </Link>
              <Link to="/registro" className="boton boton-primario">
                Crear cuenta
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
