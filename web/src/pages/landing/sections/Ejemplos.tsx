import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { publicApi } from "@/api/client";
import { NIVEL_COLOR, NIVEL_LABEL, type Nivel } from "@/types/dictamen";
import styles from "../Landing.module.css";

export function Ejemplos() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["public-corpus"],
    queryFn: publicApi.corpus
  });

  return (
    <section id="ejemplos" className={`${styles.seccion} ${styles.seccionAlterna}`}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>Ejemplos</span>
        <h2 className={styles.seccionTitulo}>
          Informes reales sobre contratos de la práctica jurídica boliviana
        </h2>
        <p className={styles.seccionIntro}>
          El corpus público muestra contratos ya analizados: cada tarjeta
          resume su rubro, índice de riesgo, nivel y cantidad de hallazgos.
        </p>

        {isLoading && <p className={styles.estadoCarga}>Cargando ejemplos…</p>}
        {isError && (
          <p className={styles.estadoError}>
            No se pudo cargar el corpus de ejemplos en este momento.
          </p>
        )}

        {data && (
          <div className={styles.ejemplosGrid}>
            {data.map((item) => {
              const nivel = item.nivel as Nivel;
              return (
                <Link
                  key={item.id}
                  to={`/ejemplos/${item.id}`}
                  className={`${styles.ejemploTarjeta} tarjeta`}
                >
                  <div className={styles.ejemploCabecera}>
                    <span className={styles.ejemploRubro}>{item.rubro}</span>
                    <span
                      className="badge"
                      style={{
                        backgroundColor: `${NIVEL_COLOR[nivel]}1f`,
                        color: NIVEL_COLOR[nivel]
                      }}
                    >
                      {NIVEL_LABEL[nivel] ?? item.nivel}
                    </span>
                  </div>
                  <h3 className={styles.ejemploTitulo}>{item.titulo}</h3>
                  <div className={styles.ejemploMetricas}>
                    <span>{item.hallazgos} hallazgos</span>
                    <span className={styles.ejemploIndice}>
                      {item.indice_riesgo}/100
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
