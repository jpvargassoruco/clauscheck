import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { usageApi } from "@/api/client";
import { useAuthStore, type Theme } from "@/store/auth";
import styles from "./AppPages.module.css";

const TEMAS: { value: Theme; label: string }[] = [
  { value: "system", label: "Sistema" },
  { value: "light", label: "Claro" },
  { value: "dark", label: "Oscuro" }
];

export default function Ajustes() {
  const theme = useAuthStore((s) => s.theme);
  const setTheme = useAuthStore((s) => s.setTheme);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const { data: uso } = useQuery({
    queryKey: ["usage"],
    queryFn: () => usageApi.get()
  });

  function handleLogout() {
    logout();
    navigate("/");
  }

  const porcentajeUso = uso
    ? Math.min(100, Math.round((uso.analisis_count / Math.max(uso.plan.analisis_mes, 1)) * 100))
    : 0;

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Ajustes</h1>
          <p>Preferencias de la cuenta {user?.email}.</p>
        </div>
      </div>

      <div className={styles.ajustesGrid}>
        <div className={`${styles.ajustesTarjeta} tarjeta`}>
          <h3>Apariencia</h3>
          <div style={{ display: "flex", gap: 8 }}>
            {TEMAS.map((t) => (
              <button
                key={t.value}
                type="button"
                className={`boton ${theme === t.value ? "boton-primario" : "boton-secundario"}`}
                onClick={() => setTheme(t.value)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className={`${styles.ajustesTarjeta} tarjeta`}>
          <h3>Uso vs. plan</h3>
          {uso ? (
            <>
              <p style={{ margin: 0 }}>
                Plan <strong>{uso.plan.nombre}</strong> — {uso.analisis_count} de{" "}
                {uso.plan.analisis_mes} análisis usados este mes ({uso.periodo}).
              </p>
              <div className={styles.usoBarra}>
                <div className={styles.usoBarraRelleno} style={{ width: `${porcentajeUso}%` }} />
              </div>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-texto-suave)" }}>
                Hasta {uso.plan.docs_max} documentos · Bs {uso.plan.precio_bob}/mes
              </p>
            </>
          ) : (
            <p>Cargando uso del plan…</p>
          )}
        </div>

        <div className={`${styles.ajustesTarjeta} tarjeta`}>
          <h3>Sesión</h3>
          <p style={{ margin: 0 }}>{user?.nombre}</p>
          <p style={{ margin: 0, color: "var(--color-texto-suave)" }}>{user?.email}</p>
          <button type="button" className="boton boton-secundario" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  );
}
