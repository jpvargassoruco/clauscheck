import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { authApi, ApiError } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import styles from "./Auth.module.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const setSession = useAuthStore((s) => s.setSession);
  const navigate = useNavigate();
  const location = useLocation();

  async function afterLogin(tokens: { access_token: string; refresh_token: string }) {
    // /auth/me exige Authorization: hay que cargar el access token en el
    // store ANTES de llamarlo (login no devuelve el user, sólo tokens).
    useAuthStore
      .getState()
      .setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
    const user = await authApi.me();
    setSession({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }, user);
    const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? "/app";
    navigate(from, { replace: true });
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const result = await authApi.login({ email, password });
      if ("mfa_required" in result) {
        setMfaToken(result.mfa_token);
      } else {
        await afterLogin(result);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo iniciar sesión.");
    } finally {
      setCargando(false);
    }
  }

  async function handleMfaSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!mfaToken) return;
    setError(null);
    setCargando(true);
    try {
      const tokens = await authApi.mfaVerify({ mfa_token: mfaToken, code: codigo });
      await afterLogin(tokens);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Código inválido.");
    } finally {
      setCargando(false);
    }
  }

  if (mfaToken) {
    return (
      <div className={styles.pantalla}>
        <div className={`${styles.tarjeta} tarjeta`}>
          <Link to="/" className={styles.marca}>
            <span className={styles.marcaClaus}>Claus</span>
            <span className={styles.marcaCheck}>Check</span>
          </Link>
          <h1 style={{ fontSize: "1.5rem" }}>Verificación en dos pasos</h1>
          <p className={styles.subtitulo}>
            Ingrese el código de 6 dígitos de su aplicación de autenticación.
          </p>

          <form className={styles.formulario} onSubmit={handleMfaSubmit}>
            <div className="campo">
              <label htmlFor="mfa-codigo">Código</label>
              <input
                id="mfa-codigo"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={6}
                required
                autoFocus
                value={codigo}
                onChange={(e) => setCodigo(e.target.value)}
              />
            </div>
            {error && <p className="error-texto">{error}</p>}
            <button type="submit" className="boton boton-primario" disabled={cargando}>
              {cargando ? "Verificando…" : "Verificar"}
            </button>
            <button
              type="button"
              className="boton boton-secundario"
              onClick={() => {
                setMfaToken(null);
                setCodigo("");
                setError(null);
              }}
            >
              Volver
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.pantalla}>
      <div className={`${styles.tarjeta} tarjeta`}>
        <Link to="/" className={styles.marca}>
          <span className={styles.marcaClaus}>Claus</span>
          <span className={styles.marcaCheck}>Check</span>
        </Link>
        <h1 style={{ fontSize: "1.5rem" }}>Iniciar sesión</h1>
        <p className={styles.subtitulo}>Acceda al panel de su organización.</p>

        <form className={styles.formulario} onSubmit={handleSubmit}>
          <div className="campo">
            <label htmlFor="login-email">Correo</label>
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="login-password">Contraseña</label>
            <input
              id="login-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="error-texto">{error}</p>}
          <button type="submit" className="boton boton-primario" disabled={cargando}>
            {cargando ? "Ingresando…" : "Ingresar"}
          </button>
        </form>

        <p className={styles.pie}>
          ¿No tiene cuenta? <Link to="/registro">Regístrese aquí</Link>.
        </p>
      </div>
    </div>
  );
}
