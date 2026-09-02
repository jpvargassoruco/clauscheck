import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi, ApiError } from "@/api/client";
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

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      const res = await authApi.register({
        email,
        password,
        nombre,
        org_nombre: orgNombre
      });
      setSession(res.access_token, res.user);
      navigate("/app", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo crear la cuenta.");
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
