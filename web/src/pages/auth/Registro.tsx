import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { authApi, publicApi, ApiError } from "@/api/client";
import { useAuthStore } from "@/store/auth";
import styles from "./Auth.module.css";

export default function Registro() {
  const [nombre, setNombre] = useState("");
  const [orgNombre, setOrgNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const setSession = useAuthStore((s) => s.setSession);
  const navigate = useNavigate();

  const { data: config, isLoading: cargandoConfig } = useQuery({
    queryKey: ["public-config"],
    queryFn: publicApi.config
  });

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const tokens = await authApi.register({
        email,
        password,
        nombre,
        org_nombre: orgNombre
      });
      // /auth/me exige Authorization: hay que cargar el access token en el
      // store ANTES de llamarlo (register no devuelve el user, sólo tokens).
      useAuthStore
        .getState()
        .setTokens({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token });
      const user = await authApi.me();
      setSession({ accessToken: tokens.access_token, refreshToken: tokens.refresh_token }, user);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo crear la cuenta.");
    } finally {
      setCargando(false);
    }
  }

  if (cargandoConfig) {
    return (
      <div className={styles.pantalla}>
        <div className={`${styles.tarjeta} tarjeta`}>
          <p className={styles.subtitulo}>Cargando…</p>
        </div>
      </div>
    );
  }

  if (config && config.registration_mode !== "open") {
    return (
      <div className={styles.pantalla}>
        <div className={`${styles.tarjeta} tarjeta`}>
          <Link to="/" className={styles.marca}>
            <span className={styles.marcaClaus}>Claus</span>
            <span className={styles.marcaCheck}>Check</span>
          </Link>
          <h1 style={{ fontSize: "1.5rem" }}>Registro por solicitud</h1>
          <p className={styles.subtitulo}>
            El registro es por solicitud. Complete el formulario y un
            administrador revisará su acceso.
          </p>
          <Link to="/solicitar-acceso" className="boton boton-primario">
            Solicitar acceso
          </Link>
          <p className={styles.pie}>
            ¿Ya tiene cuenta? <Link to="/login">Inicie sesión</Link>.
          </p>
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
        <h1 style={{ fontSize: "1.5rem" }}>Crear cuenta</h1>
        <p className={styles.subtitulo}>
          Se crea su usuario y una organización nueva, de la que será
          propietario.
        </p>

        <form className={styles.formulario} onSubmit={handleSubmit}>
          <div className="campo">
            <label htmlFor="registro-nombre">Nombre completo</label>
            <input
              id="registro-nombre"
              type="text"
              required
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="registro-org">Nombre de la organización</label>
            <input
              id="registro-org"
              type="text"
              required
              placeholder="Ej. Estudio Jurídico Pérez & Asoc."
              value={orgNombre}
              onChange={(e) => setOrgNombre(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="registro-email">Correo</label>
            <input
              id="registro-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="registro-password">Contraseña</label>
            <input
              id="registro-password"
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
            {cargando ? "Creando cuenta…" : "Crear cuenta"}
          </button>
        </form>

        <p className={styles.pie}>
          ¿Ya tiene cuenta? <Link to="/login">Inicie sesión</Link>.
        </p>
      </div>
    </div>
  );
}
