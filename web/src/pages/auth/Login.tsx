import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { authApi, ApiError } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import styles from "./Auth.module.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const setSession = useAuthStore((s) => s.setSession);
  const navigate = useNavigate();
  const location = useLocation();

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const res = await authApi.login({ email, password });
      setSession(res.access_token, res.user);
      const from =
        (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ??
        "/app";
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo iniciar sesión.");
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
