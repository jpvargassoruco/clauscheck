import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, authApi, publicApi } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import styles from "./Auth.module.css";

export default function Invitacion() {
  const { token = "" } = useParams();
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const [nombre, setNombre] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  const {
    data: preview,
    isLoading,
    error: previewError
  } = useQuery({
    queryKey: ["invitation-preview", token],
    queryFn: () => publicApi.invitationPreview(token),
    enabled: !!token,
    retry: false
  });

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const tokens = await publicApi.acceptInvitation(token, { nombre, password });
      useAuthStore
        .getState()
        .setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      const user = await authApi.me();
      setSession({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }, user);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo aceptar la invitación.");
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className={styles.pantalla}>
      <div className={`${styles.tarjeta} tarjeta`}>
        <Link to="/" className={styles.marca}>
          <span className={styles.marcaClaus}>Claus</span>
          <span className={styles.marcaCheck}>Check</span>
        </Link>

        {isLoading && <p className={styles.subtitulo}>Cargando invitación…</p>}

        {previewError && (
          <>
            <h1 style={{ fontSize: "1.5rem" }}>Invitación no válida</h1>
            <p className={styles.subtitulo}>
              {previewError instanceof ApiError
                ? previewError.detail
                : "No se pudo cargar la invitación."}
            </p>
            <Link to="/login" className="boton boton-secundario">
              Ir a iniciar sesión
            </Link>
          </>
        )}

        {preview && preview.expired && (
          <>
            <h1 style={{ fontSize: "1.5rem" }}>Invitación expirada</h1>
            <p className={styles.subtitulo}>
              Este enlace de invitación ya venció. Pida al administrador de su
              organización que le envíe una nueva.
            </p>
          </>
        )}

        {preview && preview.accepted && !preview.expired && (
          <>
            <h1 style={{ fontSize: "1.5rem" }}>Invitación ya aceptada</h1>
            <p className={styles.subtitulo}>Esta invitación ya fue utilizada.</p>
            <Link to="/login" className="boton boton-secundario">
              Ir a iniciar sesión
            </Link>
          </>
        )}

        {preview && !preview.expired && !preview.accepted && (
          <>
            <h1 style={{ fontSize: "1.5rem" }}>Unirse a {preview.org_nombre}</h1>
            <p className={styles.subtitulo}>
              Fue invitado como <strong>{preview.role}</strong> con el correo{" "}
              {preview.email}. Complete su nombre y una contraseña para activar
              su cuenta.
            </p>

            <form className={styles.formulario} onSubmit={handleSubmit}>
              <div className="campo">
                <label htmlFor="inv-nombre">Nombre completo</label>
                <input
                  id="inv-nombre"
                  type="text"
                  required
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>
              <div className="campo">
                <label htmlFor="inv-password">Contraseña</label>
                <input
                  id="inv-password"
                  type="password"
                  required
                  minLength={8}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              {error && <p className="error-texto">{error}</p>}
              <button type="submit" className="boton boton-primario" disabled={cargando}>
                {cargando ? "Creando cuenta…" : "Unirme"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
