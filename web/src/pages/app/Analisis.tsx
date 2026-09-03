import { useMutation, useQuery, type UseMutationResult } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { analysesApi, documentsApi, ApiError } from "@/api/client";
import type { DocumentSummary } from "@/types/domain";
import { useState } from "react";
import styles from "./AppPages.module.css";

interface FilaDocumentoProps {
  doc: DocumentSummary;
  analizarMutacion: UseMutationResult<{ id: string; status: string }, unknown, string>;
}

function FilaDocumento({ doc, analizarMutacion }: FilaDocumentoProps) {
  const { data: estimacion, isLoading } = useQuery({
    queryKey: ["document-estimate", doc.id],
    queryFn: () => documentsApi.estimate(doc.id)
  });

  const enCurso = analizarMutacion.isPending && analizarMutacion.variables === doc.id;
  const bloqueado = estimacion ? !estimacion.dentro_del_plan : false;

  return (
    <div className={`${styles.filaItem} tarjeta`}>
      <div className={styles.filaInfo}>
        <h3>{doc.titulo}</h3>
        <div className={styles.filaMeta}>
          <span>{doc.tipo_contrato}</span>
          <span>{doc.rubro}</span>
          <span>{doc.palabras.toLocaleString("es-BO")} palabras</span>
        </div>
        {isLoading && <p style={{ margin: "6px 0 0", fontSize: "0.82rem" }}>Calculando estimación…</p>}
        {estimacion && (
          <p
            style={{
              margin: "6px 0 0",
              fontSize: "0.82rem",
              color: bloqueado ? "var(--nivel-critico)" : "var(--color-texto-suave)"
            }}
          >
            {bloqueado
              ? estimacion.motivo
              : `≈ ${estimacion.tokens_estimados.toLocaleString("es-BO")} tokens · ` +
                `≈ USD ${estimacion.costo_estimado_usd.toFixed(4)} estimados`}
          </p>
        )}
      </div>
      <div className={styles.filaAcciones}>
        <button
          type="button"
          className="boton boton-primario"
          onClick={() => analizarMutacion.mutate(doc.id)}
          disabled={analizarMutacion.isPending || bloqueado}
          title={bloqueado ? estimacion?.motivo : undefined}
        >
          {enCurso ? "Encolando…" : bloqueado ? "Fuera de plan" : "Analizar"}
        </button>
      </div>
    </div>
  );
}

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

  const documentosListos = data?.filter((d) => d.ocr_status === "ready") ?? [];

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
            <FilaDocumento key={doc.id} doc={doc} analizarMutacion={analizarMutacion} />
          ))}
        </div>
      )}
    </div>
  );
}
