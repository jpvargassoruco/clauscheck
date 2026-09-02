import { Link, NavLink, Outlet } from "react-router-dom";
import styles from "./AppShell.module.css";

const navItems = [
  { to: "/admin/proveedores", label: "Proveedores" },
  { to: "/admin/normativa", label: "Normativa" },
  { to: "/admin/organizaciones", label: "Organizaciones" },
  { to: "/admin/planes", label: "Planes" }
];

export function AdminShell() {
  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.marca}>
          <span className={styles.marcaClaus}>Claus</span>
          <span className={styles.marcaCheck}>Check</span>
          <div style={{ fontSize: "0.7rem", fontWeight: 600, color: "var(--color-texto-suave)" }}>
            Panel de administración
          </div>
        </div>

        <nav className={styles.nav} aria-label="Navegación de administración">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? `${styles.navLink} ${styles.navLinkActivo}` : styles.navLink
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarPie}>
          <Link to="/app" className="boton boton-secundario">
            Volver a la app
          </Link>
        </div>
      </aside>

      <main className={styles.contenido}>
        <Outlet />
      </main>
    </div>
  );
}
