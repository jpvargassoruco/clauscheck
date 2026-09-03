import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { ApiError, authApi, usageApi } from "@/api/client";
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
  const setUser = useAuthStore((s) => s.setUser);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const [mfaSetup, setMfaSetup] = useState<{ secret: string; otpauth_url: string; qr: string } | null>(
    null
  );
  const [codigo, setCodigo] = useState("");
  const [mfaError, setMfaError] = useState<string | null>(null);
  const [mostrandoDesactivar, setMostrandoDesactivar] = useState(false);

  const { data: uso } = useQuery({
    queryKey: ["usage"],
    queryFn: () => usageApi.get()
  });

  async function refrescarUsuario() {
    const actualizado = await authApi.me();
    setUser(actualizado);
  }

  const setupMutacion = useMutation({
    mutationFn: authApi.mfaSetup,
    onSuccess: (data) => {
      setMfaSetup(data);
      setMfaError(null);
    },
    onError: (err) => setMfaError(err instanceof ApiError ? err.detail : "No se pudo iniciar MFA.")
  });

  const enableMutacion = useMutation({
    mutationFn: (code: string) => authApi.mfaEnable(code),
    onSuccess: async () => {
      setMfaSetup(null);
      setCodigo("");
      setMfaError(null);
      await refrescarUsuario();
    },
    onError: (err) => setMfaError(err instanceof ApiError ? err.detail : "Código inválido.")
  });

  const disableMutacion = useMutation({
    mutationFn: (code: string) => authApi.mfaDisable(code),
    onSuccess: async () => {
      setMostrandoDesactivar(false);
      setCodigo("");
      setMfaError(null);
      await refrescarUsuario();
    },
    onError: (err) => setMfaError(err instanceof ApiError ? err.detail : "Código inválido.")
  });

  function handleLogout() {
    logout();
    navigate("/");
  }

  const porcentajeUso = uso
    ? Math.min(100, Math.round((uso.analisis_count / Math.max(uso.analisis_mes, 1)) * 100))
    : 0;
  const porcentajePalabras = uso
    ? Math.min(100, Math.round((uso.palabras_count / Math.max(uso.palabras_mes, 1)) * 100))
    : 0;

  const esSuperadminSinMfa = !!user?.is_superadmin && !user.mfa_enabled;

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Ajustes</h1>
          <p>Preferencias de la cuenta {user?.email}.</p>
        </div>
      </div>

      {esSuperadminSinMfa && (
        <p className="error-texto">
          Su cuenta de superadmin no tiene la autenticación en dos pasos (MFA)
          activada. Se recomienda activarla en la tarjeta «Seguridad».
        </p>
      )}

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
                Plan <strong>{uso.plan_code}</strong> — {uso.analisis_count} de{" "}
                {uso.analisis_mes} análisis usados este mes ({uso.periodo}).
              </p>
              <div className={styles.usoBarra}>
                <div className={styles.usoBarraRelleno} style={{ width: `${porcentajeUso}%` }} />
              </div>
              <p style={{ margin: 0 }}>
                {uso.palabras_count.toLocaleString("es-BO")} de{" "}
                {uso.palabras_mes.toLocaleString("es-BO")} palabras usadas este mes.
              </p>
              <div className={styles.usoBarra}>
                <div
                  className={styles.usoBarraRelleno}
                  style={{
                    width: `${porcentajePalabras}%`,
                    background: porcentajePalabras >= 80 ? "var(--nivel-critico)" : undefined
                  }}
                />
              </div>
            </>
          ) : (
            <p>Cargando uso del plan…</p>
          )}
        </div>

        <div className={`${styles.ajustesTarjeta} tarjeta`}>
          <h3>Seguridad — autenticación en dos pasos (MFA)</h3>

          {user?.mfa_enabled ? (
            <>
              <p style={{ margin: 0 }}>La autenticación en dos pasos está activa.</p>
              {!mostrandoDesactivar ? (
                <button
                  type="button"
                  className="boton boton-secundario"
                  onClick={() => {
                    setMostrandoDesactivar(true);
                    setMfaError(null);
                  }}
                >
                  Desactivar MFA
                </button>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  <div className="campo">
                    <label htmlFor="mfa-disable-codigo">Código de la app de autenticación</label>
                    <input
                      id="mfa-disable-codigo"
                      type="text"
                      inputMode="numeric"
                      maxLength={6}
                      value={codigo}
                      onChange={(e) => setCodigo(e.target.value)}
                    />
                  </div>
                  {mfaError && <p className="error-texto">{mfaError}</p>}
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      type="button"
                      className="boton boton-primario"
                      disabled={disableMutacion.isPending}
                      onClick={() => disableMutacion.mutate(codigo)}
                    >
                      {disableMutacion.isPending ? "Desactivando…" : "Confirmar"}
                    </button>
                    <button
                      type="button"
                      className="boton boton-secundario"
                      onClick={() => {
                        setMostrandoDesactivar(false);
                        setCodigo("");
                        setMfaError(null);
                      }}
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : mfaSetup ? (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <p style={{ margin: 0 }}>
                Escanee el código QR con su aplicación de autenticación (Google
                Authenticator, Authy, etc.) o ingrese el secreto manualmente.
              </p>
              <img
                src={mfaSetup.qr}
                alt="Código QR para configurar MFA"
                style={{ width: 180, height: 180, alignSelf: "center" }}
              />
              <p style={{ margin: 0, fontSize: "0.85rem", wordBreak: "break-all" }}>
                Secreto: <code>{mfaSetup.secret}</code>
              </p>
              <div className="campo">
                <label htmlFor="mfa-enable-codigo">Código generado por la app</label>
                <input
                  id="mfa-enable-codigo"
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                />
              </div>
              {mfaError && <p className="error-texto">{mfaError}</p>}
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  type="button"
                  className="boton boton-primario"
                  disabled={enableMutacion.isPending}
                  onClick={() => enableMutacion.mutate(codigo)}
                >
                  {enableMutacion.isPending ? "Activando…" : "Confirmar activación"}
                </button>
                <button
                  type="button"
                  className="boton boton-secundario"
                  onClick={() => {
                    setMfaSetup(null);
                    setCodigo("");
                    setMfaError(null);
                  }}
                >
                  Cancelar
                </button>
              </div>
            </div>
          ) : (
            <>
              <p style={{ margin: 0 }}>
                Agregue una capa extra de seguridad a su cuenta con un código
                de un solo uso generado por una app de autenticación.
              </p>
              <button
                type="button"
                className="boton boton-primario"
                disabled={setupMutacion.isPending}
                onClick={() => setupMutacion.mutate()}
              >
                {setupMutacion.isPending ? "Generando…" : "Activar MFA"}
              </button>
              {mfaError && <p className="error-texto">{mfaError}</p>}
            </>
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
