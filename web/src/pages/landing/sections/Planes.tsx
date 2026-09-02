import { Link } from "react-router-dom";
import styles from "../Landing.module.css";

const planes = [
  {
    codigo: "free",
    nombre: "Free",
    precio: "Bs 0",
    periodo: "/mes",
    destacado: false,
    items: [
      "3 análisis por mes",
      "Hasta 10 documentos",
      "1 organización",
      "Dictamen completo con citas verificadas",
      "Soporte por comunidad"
    ]
  },
  {
    codigo: "pro",
    nombre: "Pro",
    precio: "Bs 149",
    periodo: "/mes",
    destacado: true,
    items: [
      "30 análisis por mes",
      "Hasta 150 documentos",
      "Hasta 5 usuarios por organización",
      "Historial completo y exportación",
      "Soporte prioritario"
    ]
  },
  {
    codigo: "despacho",
    nombre: "Despacho",
    precio: "Bs 399",
    periodo: "/mes",
    destacado: false,
    items: [
      "Análisis ilimitados",
      "Documentos ilimitados",
      "Usuarios ilimitados",
      "Organizaciones múltiples",
      "Soporte dedicado y onboarding"
    ]
  }
];

export function Planes() {
  return (
    <section id="planes" className={styles.seccion}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>Planes</span>
        <h2 className={styles.seccionTitulo}>
          Un modelo SaaS accesible para despachos, startups y empresas
        </h2>
        <p className={styles.seccionIntro}>
          Precios de referencia en bolivianos. Los montos finales se
          confirman al activar la suscripción.
        </p>
        <div className={styles.planesGrid}>
          {planes.map((p) => (
            <div
              key={p.codigo}
              className={`${styles.planTarjeta} tarjeta ${p.destacado ? styles.planDestacado : ""}`}
            >
              <h3 className={styles.planNombre}>{p.nombre}</h3>
              <div className={styles.planPrecio}>
                {p.precio}
                <span>{p.periodo}</span>
              </div>
              <ul className={styles.planLista}>
                {p.items.map((i) => (
                  <li key={i}>{i}</li>
                ))}
              </ul>
              <Link
                to="/registro"
                className={`boton ${p.destacado ? "boton-acento" : "boton-secundario"}`}
              >
                Elegir {p.nombre}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
