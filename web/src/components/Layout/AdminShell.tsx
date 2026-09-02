import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import styles from "./AppShell.module.css";

const navItems = [
  { to: "/admin/proveedores", label: "Proveedores" },
  { to: "/admin/normativa", label: "Normativa" },
  { to: "/admin/organizaciones", label: "Organizaciones" },
  { to: "/admin/planes", label: "Planes" },
  { to: "/admin/solicitudes", label: "Solicitudes" }
];

export function AdminShell() {
  const user = useAuthStore((s) => s.user);
  const mostrarAvisoMfa = !!user?.is_superadmin && !user.mfa_enabled;

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
        {mostrarAvisoMfa && (
          <p className="error-texto" style={{ marginBottom: 16 }}>
            Su cuenta de superadmin no tiene la autenticación en dos pasos
            (MFA) activada. Actívela en Ajustes de la app.
          </p>
        )}
        <Outlet />
      </main>
    </div>
  );
}
