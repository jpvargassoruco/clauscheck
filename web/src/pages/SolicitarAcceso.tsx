import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { ApiError, publicApi } from "@/api/client";
import styles from "./auth/Auth.module.css";

export default function SolicitarAcceso() {
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [organizacion, setOrganizacion] = useState("");
  const [telefono, setTelefono] = useState("");
  const [motivo, setMotivo] = useState("");
  const [website, setWebsite] = useState(""); // honeypot: debe quedar vacío
  const [error, setError] = useState<string | null>(null);
  const [enviado, setEnviado] = useState(false);
  const [cargando, setCargando] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setCargando(true);
    try {
      await publicApi.createAccessRequest({
        nombre,
        email,
        organizacion,
        telefono,
        motivo,
        website
      });
      setEnviado(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo enviar la solicitud.");
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

        {enviado ? (
          <>
            <h1 style={{ fontSize: "1.5rem" }}>Solicitud enviada</h1>
            <p className={styles.subtitulo}>
              Recibimos su solicitud de acceso. Le enviaremos un correo con la
              respuesta apenas un administrador la revise.
            </p>
            <Link to="/" className="boton boton-secundario">
              Volver al inicio
            </Link>
          </>
        ) : (
          <>
            <h1 style={{ fontSize: "1.5rem" }}>Solicitar acceso</h1>
            <p className={styles.subtitulo}>
              Cuéntenos sobre su despacho u organización; un administrador
              revisará su solicitud y le enviará una invitación.
            </p>

            <form className={styles.formulario} onSubmit={handleSubmit}>
              <div className="campo">
                <label htmlFor="sa-nombre">Nombre completo</label>
                <input
                  id="sa-nombre"
                  type="text"
                  required
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                />
              </div>
              <div className="campo">
                <label htmlFor="sa-email">Correo</label>
                <input
                  id="sa-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="campo">
                <label htmlFor="sa-org">Organización</label>
                <input
                  id="sa-org"
                  type="text"
                  required
                  placeholder="Ej. Estudio Jurídico Pérez & Asoc."
                  value={organizacion}
                  onChange={(e) => setOrganizacion(e.target.value)}
                />
              </div>
              <div className="campo">
                <label htmlFor="sa-telefono">Teléfono</label>
                <input
                  id="sa-telefono"
                  type="tel"
                  value={telefono}
                  onChange={(e) => setTelefono(e.target.value)}
                />
              </div>
              <div className="campo">
                <label htmlFor="sa-motivo">Motivo de la solicitud</label>
                <textarea
                  id="sa-motivo"
                  rows={3}
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                />
              </div>

              {/* Honeypot anti-spam: invisible para personas, los bots que
                  autocompletan formularios sí suelen rellenarlo. */}
              <div style={{ position: "absolute", left: "-9999px" }} aria-hidden="true">
                <label htmlFor="sa-website">No completar este campo</label>
                <input
                  id="sa-website"
                  type="text"
                  tabIndex={-1}
                  autoComplete="off"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                />
              </div>

              {error && <p className="error-texto">{error}</p>}
              <button type="submit" className="boton boton-primario" disabled={cargando}>
                {cargando ? "Enviando…" : "Enviar solicitud"}
              </button>
            </form>

            <p className={styles.pie}>
              ¿Ya tiene cuenta? <Link to="/login">Inicie sesión</Link>.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
