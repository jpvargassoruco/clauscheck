import styles from "../Landing.module.css";

const equipo = [
  "Basilio Soliz Ribera",
  "Roxana Vaca Ibáñez",
  "Lilian Marcela Reynolds Aparicio",
  "Ana Katherin Ñandauca Soliz",
  "Katherine Nikol Siles Rojas",
  "Eloisa Milena Apaza Ribera",
  "Leslie Alondra Apaza Ribera"
];

function iniciales(nombre: string): string {
  const partes = nombre.split(" ");
  return `${partes[0][0]}${partes[1]?.[0] ?? ""}`.toUpperCase();
}

export function Equipo() {
  return (
    <section id="equipo" className={`${styles.seccion} ${styles.seccionAlterna}`}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>Equipo</span>
        <h2 className={styles.seccionTitulo}>
          Un equipo de Derecho Informático de la UAGRM
        </h2>
        <p className={styles.seccionIntro}>
          ClausCheck nace en la Carrera de Derecho de la Universidad
          Autónoma Gabriel René Moreno, como proyecto de la materia Derecho
          Informático, bajo la guía del docente Honel Justiniano — Grupo
          F-1.
        </p>
        <div className={styles.equipoGrid}>
          {equipo.map((nombre) => (
            <div key={nombre} className={`${styles.equipoTarjeta} tarjeta`}>
              <span className={styles.equipoAvatar} aria-hidden="true">
                {iniciales(nombre)}
              </span>
              <p className={styles.equipoNombre}>{nombre}</p>
              <p className={styles.equipoRol}>UAGRM · Derecho</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
