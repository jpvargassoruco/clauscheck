import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import { ThemeToggle } from "./ThemeToggle";
import styles from "./AppShell.module.css";

const navItems = [
  { to: "/app/documentos", label: "Documentos" },
  { to: "/app/analisis", label: "Análisis" },
  { to: "/app/historial", label: "Historial" },
  { to: "/app/ajustes", label: "Ajustes" }
];

export function AppShell() {
  const user = useAuthStore((s) => s.user);
  const currentOrgId = useAuthStore((s) => s.currentOrgId);
  const setCurrentOrg = useAuthStore((s) => s.setCurrentOrg);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const memberships = user?.orgs ?? [];

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.marca}>
          <span className={styles.marcaClaus}>Claus</span>
          <span className={styles.marcaCheck}>Check</span>
        </div>

        <label className={styles.orgSwitcherLabel} htmlFor="org-switcher">
          Organización
        </label>
        <select
          id="org-switcher"
          className={styles.orgSwitcher}
          value={currentOrgId ?? ""}
          onChange={(e) => setCurrentOrg(e.target.value)}
        >
          {memberships.map((m) => (
            <option key={m.org.id} value={m.org.id}>
              {m.org.nombre}
            </option>
          ))}
        </select>

        <nav className={styles.nav} aria-label="Navegación de la aplicación">
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
          {user?.is_superadmin && (
            <NavLink to="/admin" className={styles.navLink}>
              Administración
            </NavLink>
          )}
        </nav>

        <div className={styles.sidebarPie}>
          <ThemeToggle />
          <button type="button" className="boton boton-secundario" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className={styles.contenido}>
        <Outlet />
      </main>
    </div>
  );
}
