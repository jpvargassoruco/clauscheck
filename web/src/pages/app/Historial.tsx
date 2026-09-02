import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { analysesApi } from "@/api/client";
import type { AnalysisStatus } from "@/types/domain";
import styles from "./AppPages.module.css";

const ESTADO_LABEL: Record<AnalysisStatus, string> = {
  queued: "En cola",
  running: "Procesando",
  done: "Completado",
  failed: "Falló"
};

const ESTADO_CLASE: Record<AnalysisStatus, string> = {
  queued: styles.estadoPending,
  running: styles.estadoPending,
  done: styles.estadoReady,
  failed: styles.estadoFailed
};

export default function Historial() {
  const { data, isLoading } = useQuery({
    queryKey: ["analyses"],
    queryFn: () => analysesApi.list()
  });

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Historial</h1>
          <p>Todos los análisis ejecutados por su organización.</p>
        </div>
      </div>

      {isLoading && <p>Cargando historial…</p>}

      {data && data.length === 0 && (
        <div className={`${styles.vacio} tarjeta`}>
          Todavía no se ejecutó ningún análisis.
        </div>
      )}

      {data && data.length > 0 && (
        <div className={styles.lista}>
          {data.map((a) => (
            <Link
              key={a.id}
              to={`/app/analisis/${a.id}`}
              className={`${styles.filaItem} tarjeta`}
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <div className={styles.filaInfo}>
                <h3>Análisis {a.id.slice(0, 8)}</h3>
                <div className={styles.filaMeta}>
                  <span>{new Date(a.created_at).toLocaleString("es-BO")}</span>
                  {a.dictamen && (
                    <span>
                      Índice {a.dictamen.indice_riesgo}/100 · {a.dictamen.nivel}
                    </span>
                  )}
                </div>
              </div>
              <span className={`${styles.estadoBadge} ${ESTADO_CLASE[a.status]}`}>
                {ESTADO_LABEL[a.status]}
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
