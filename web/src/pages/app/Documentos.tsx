import { useRef, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { documentsApi, ApiError } from "@/api/client";
import type { OcrStatus } from "@/types/domain";
import styles from "./AppPages.module.css";

const ESTADO_LABEL: Record<OcrStatus, string> = {
  pending: "Procesando",
  ready: "Listo",
  failed: "Falló"
};

const ESTADO_CLASE: Record<OcrStatus, string> = {
  pending: styles.estadoPending,
  ready: styles.estadoReady,
  failed: styles.estadoFailed
};

export default function Documentos() {
  const queryClient = useQueryClient();
  const [modo, setModo] = useState<"archivo" | "texto">("archivo");
  const [titulo, setTitulo] = useState("");
  const [texto, setTexto] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsApi.list()
  });

  const crearMutacion = useMutation({
    mutationFn: async () => {
      if (modo === "archivo") {
        if (!archivo) throw new Error("Seleccione un archivo.");
        return documentsApi.createFromFile(archivo, titulo || archivo.name);
      }
      return documentsApi.createFromText(titulo || "Documento sin título", texto);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
      setTitulo("");
      setTexto("");
      setArchivo(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.detail : "No se pudo subir el documento.");
    }
  });

  const eliminarMutacion = useMutation({
    mutationFn: (id: string) => documentsApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] })
  });

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    crearMutacion.mutate();
  }

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Documentos</h1>
          <p>Contratos cargados por su organización, con su estado de OCR.</p>
        </div>
      </div>

      <form className={`${styles.panelSubida} tarjeta`} onSubmit={handleSubmit}>
        <div className={styles.tabsModo}>
          <button
            type="button"
            className={`${styles.tabModo} ${modo === "archivo" ? styles.tabModoActivo : ""}`}
            onClick={() => setModo("archivo")}
          >
            Subir archivo
          </button>
          <button
            type="button"
            className={`${styles.tabModo} ${modo === "texto" ? styles.tabModoActivo : ""}`}
            onClick={() => setModo("texto")}
          >
            Pegar texto
          </button>
        </div>

        <div className="campo">
          <label htmlFor="doc-titulo">Título</label>
          <input
            id="doc-titulo"
            type="text"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            placeholder="Ej. Contrato de anticrético — tienda comercial"
          />
        </div>

        {modo === "archivo" ? (
          <div className="campo">
            <label htmlFor="doc-archivo">Archivo (PDF, PNG, JPG, DOCX o TXT)</label>
            <input
              id="doc-archivo"
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.docx,.txt"
              onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
            />
          </div>
        ) : (
          <div className="campo">
            <label htmlFor="doc-texto">Texto del contrato</label>
            <textarea
              id="doc-texto"
              rows={8}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Pegue aquí el texto completo del contrato…"
            />
          </div>
        )}

        {error && <p className="error-texto">{error}</p>}

        <button type="submit" className="boton boton-primario" disabled={crearMutacion.isPending}>
          {crearMutacion.isPending ? "Subiendo…" : "Subir documento"}
        </button>
      </form>

      {isLoading && <p>Cargando documentos…</p>}

      {data && data.length === 0 && (
        <div className={`${styles.vacio} tarjeta`}>
          Aún no hay documentos. Suba el primer contrato arriba.
        </div>
      )}

      {data && data.length > 0 && (
        <div className={styles.lista}>
          {data.map((doc) => (
            <div key={doc.id} className={`${styles.filaItem} tarjeta`}>
              <div className={styles.filaInfo}>
                <h3>{doc.titulo}</h3>
                <div className={styles.filaMeta}>
                  <span>{doc.tipo_contrato}</span>
                  <span>{doc.rubro}</span>
                  <span>{doc.palabras.toLocaleString("es-BO")} palabras</span>
                  <span>{new Date(doc.created_at).toLocaleDateString("es-BO")}</span>
                </div>
              </div>
              <div className={styles.filaAcciones}>
                <span className={`${styles.estadoBadge} ${ESTADO_CLASE[doc.ocr_status]}`}>
                  {ESTADO_LABEL[doc.ocr_status]}
                </span>
                <button
                  type="button"
                  className="boton boton-secundario"
                  onClick={() => eliminarMutacion.mutate(doc.id)}
                  disabled={eliminarMutacion.isPending}
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
