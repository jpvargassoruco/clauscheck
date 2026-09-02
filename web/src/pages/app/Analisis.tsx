import { useMutation, useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { analysesApi, documentsApi, ApiError } from "@/api/client";
import { useState } from "react";
import styles from "./AppPages.module.css";

export default function Analisis() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsApi.list()
  });

  const analizarMutacion = useMutation({
    mutationFn: (documentId: string) => analysesApi.create(documentId),
    onSuccess: (res) => navigate(`/app/analisis/${res.id}`),
    onError: (err) =>
      setError(err instanceof ApiError ? err.detail : "No se pudo iniciar el análisis.")
  });

  const documentosListos = data?.items.filter((d) => d.ocr_status === "ready") ?? [];

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Análisis</h1>
          <p>Elija un documento listo y ejecute el motor de siete etapas.</p>
        </div>
      </div>

      {error && <p className="error-texto">{error}</p>}
      {isLoading && <p>Cargando documentos…</p>}

      {data && documentosListos.length === 0 && (
        <div className={`${styles.vacio} tarjeta`}>
          No hay documentos listos para analizar. Suba un contrato en
          Documentos y espere a que el OCR quede en estado «Listo».
        </div>
      )}

      {documentosListos.length > 0 && (
        <div className={styles.lista}>
          {documentosListos.map((doc) => (
            <div key={doc.id} className={`${styles.filaItem} tarjeta`}>
              <div className={styles.filaInfo}>
                <h3>{doc.titulo}</h3>
                <div className={styles.filaMeta}>
                  <span>{doc.tipo_contrato}</span>
                  <span>{doc.rubro}</span>
                </div>
              </div>
              <div className={styles.filaAcciones}>
                <button
                  type="button"
                  className="boton boton-primario"
                  onClick={() => analizarMutacion.mutate(doc.id)}
                  disabled={analizarMutacion.isPending}
                >
                  {analizarMutacion.isPending ? "Encolando…" : "Analizar"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
