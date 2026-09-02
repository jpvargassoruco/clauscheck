import { useState, type FormEvent } from "react";
import styles from "../Landing.module.css";

const CONTACTO_EMAIL = "contacto@clauscheck.bo";

export function Contacto() {
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [mensaje, setMensaje] = useState("");

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const asunto = encodeURIComponent(`Contacto ClausCheck — ${nombre || "sin nombre"}`);
    const cuerpo = encodeURIComponent(
      `Nombre: ${nombre}\nCorreo: ${email}\n\n${mensaje}`
    );
    window.location.href = `mailto:${CONTACTO_EMAIL}?subject=${asunto}&body=${cuerpo}`;
  }

  return (
    <section id="contacto" className={styles.seccion}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>Contacto</span>
        <h2 className={styles.seccionTitulo}>Hablemos de su despacho o empresa</h2>
        <div className={styles.contactoGrid}>
          <div>
            <p className={styles.seccionIntro}>
              Escríbanos para una demo, una alianza institucional o dudas
              sobre planes. Respondemos en horario laboral (Santa Cruz de
              la Sierra, Bolivia).
            </p>
            <p>
              Correo directo:{" "}
              <a href={`mailto:${CONTACTO_EMAIL}`}>{CONTACTO_EMAIL}</a>
            </p>
          </div>

          <form className={`${styles.contactoForm} tarjeta`} onSubmit={handleSubmit} style={{ padding: 24 }}>
            <div className="campo">
              <label htmlFor="contacto-nombre">Nombre</label>
              <input
                id="contacto-nombre"
                type="text"
                required
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </div>
            <div className="campo">
              <label htmlFor="contacto-email">Correo</label>
              <input
                id="contacto-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="campo">
              <label htmlFor="contacto-mensaje">Mensaje</label>
              <textarea
                id="contacto-mensaje"
                rows={4}
                required
                value={mensaje}
                onChange={(e) => setMensaje(e.target.value)}
              />
            </div>
            <button type="submit" className="boton boton-primario">
              Enviar mensaje
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
