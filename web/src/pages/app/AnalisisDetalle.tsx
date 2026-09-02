import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { analysesApi, documentsApi } from "@/api/client";
import { Dictamen } from "@/components/Dictamen/Dictamen";
import styles from "./AppPages.module.css";

const ETAPAS = [
  "Normaliza el texto",
  "Separa las cláusulas",
  "Identifica a las partes",
  "Detecta patrones de riesgo",
  "Contrasta contra la norma",
  "Pondera el impacto por parte",
  "Redacta el dictamen"
];

export default function AnalisisDetalle() {
  const { id } = useParams<{ id: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ["analysis", id],
    queryFn: () => analysesApi.get(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 2000 : false;
    }
  });

  const { data: documento } = useQuery({
    queryKey: ["document", data?.document_id],
    queryFn: () => documentsApi.get(data!.document_id),
    enabled: Boolean(data?.document_id)
  });

  if (isLoading || !data) {
    return <p>Cargando análisis…</p>;
  }

  const enCurso = data.status === "queued" || data.status === "running";

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Análisis</h1>
          <p>{documento?.titulo ?? "Contrato en revisión"}</p>
        </div>
      </div>

      {enCurso && (
        <div className={`${styles.progreso} tarjeta`}>
          {ETAPAS.map((etiqueta, i) => {
            const numeroEtapa = i + 1;
            const hecha = data.etapa > numeroEtapa;
            const activa = data.etapa === numeroEtapa - 1 || data.etapa === numeroEtapa;
            return (
              <div key={etiqueta} className={styles.progresoEtapa}>
                <span
                  className={`${styles.progresoPunto} ${hecha ? styles.progresoPuntoHecho : ""} ${activa && !hecha ? styles.progresoPuntoActivo : ""}`}
                >
                  {hecha ? "✓" : numeroEtapa}
                </span>
                <span
                  className={`${styles.progresoTexto} ${hecha ? styles.progresoTextoHecho : ""}`}
                >
                  {etiqueta}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {data.status === "failed" && (
        <div className="tarjeta" style={{ padding: 20 }}>
          <p className="error-texto">
            El análisis falló: {data.error ?? "error desconocido."}
          </p>
        </div>
      )}

      {data.status === "done" && data.dictamen && (
        <Dictamen dictamen={data.dictamen} tituloDocumento={documento?.titulo} />
      )}
    </div>
  );
}
