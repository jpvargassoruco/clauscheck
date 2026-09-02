import { Link } from "react-router-dom";
import styles from "../Landing.module.css";

const planes = [
  {
    codigo: "personal",
    nombre: "Personal",
    precio: "Bs 149",
    periodo: "/mes",
    destacado: false,
    items: [
      "Abogado independiente o emprendedor",
      "Hasta 20 análisis por mes",
      "1 usuario",
      "Informe de revisión asistida con citas verificadas",
      "Exportación a .docx"
    ]
  },
  {
    codigo: "despacho",
    nombre: "Despacho",
    precio: "Bs 490",
    periodo: "/mes",
    destacado: true,
    items: [
      "De 2 a 8 abogados",
      "Hasta 100 análisis por mes",
      "5 usuarios",
      "Expedientes y playbook por despacho",
      "Informe firmado por abogado (próximamente)"
    ]
  },
  {
    codigo: "empresa",
    nombre: "Empresa",
    precio: "Bs 1.200",
    periodo: "/mes",
    destacado: false,
    items: [
      "Área legal interna, inmobiliaria, constructora",
      "Hasta 300 análisis por mes",
      "15 usuarios",
      "Acceso por API",
      "Auditoría y soporte prioritario"
    ]
  },
  {
    codigo: "suelto",
    nombre: "Suelto",
    precio: "Bs 39",
    periodo: "/contrato",
    destacado: false,
    items: [
      "Persona que va a firmar",
      "1 análisis, sin necesidad de cuenta",
      "Pago por QR",
      "Informe con aviso de responsabilidad"
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
          Precios de lanzamiento en bolivianos, sujetos a cambio. Los montos
          finales se confirman al activar la suscripción.
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
