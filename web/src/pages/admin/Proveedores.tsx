import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, ApiError } from "@/api/client";
import type { LlmProvider } from "@/types/domain";
import styles from "../app/AppPages.module.css";

const KIND_OPTIONS: LlmProvider["kind"][] = ["openai_compat", "anthropic"];
const CODE_OPTIONS: LlmProvider["code"][] = [
  "deepseek",
  "moonshot",
  "openrouter",
  "anthropic"
];

export default function Proveedores() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    code: "deepseek" as LlmProvider["code"],
    kind: "openai_compat" as LlmProvider["kind"],
    base_url: "https://api.deepseek.com",
    model: "deepseek-chat",
    api_key: ""
  });
  const [error, setError] = useState<string | null>(null);
  const [resultados, setResultados] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ["admin-providers"],
    queryFn: adminApi.providers.list
  });

  const crearMutacion = useMutation({
    mutationFn: () => adminApi.providers.create(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-providers"] });
      setForm((f) => ({ ...f, api_key: "" }));
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.detail : "No se pudo crear el proveedor.")
  });

  const toggleMutacion = useMutation({
    mutationFn: (p: LlmProvider) =>
      adminApi.providers.update(p.id, { enabled: !p.enabled }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-providers"] })
  });

  const defaultMutacion = useMutation({
    mutationFn: (p: LlmProvider) =>
      adminApi.providers.update(p.id, { is_default: true }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-providers"] })
  });

  const eliminarMutacion = useMutation({
    mutationFn: (id: string) => adminApi.providers.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-providers"] })
  });

  const testMutacion = useMutation({
    mutationFn: (id: string) => adminApi.providers.test(id),
    onSuccess: (res, id) =>
      setResultados((r) => ({
        ...r,
        [id]: res.ok ? "Conexión OK" : `Falló: ${res.detail ?? "sin detalle"}`
      })),
    onError: (err, id) =>
      setResultados((r) => ({
        ...r,
        [id]: err instanceof ApiError ? err.detail : "Error al probar"
      }))
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
          <h1>Proveedores de IA</h1>
          <p>Adaptadores de LLM disponibles para el motor de análisis.</p>
        </div>
      </div>

      <form className={`${styles.panelSubida} tarjeta`} onSubmit={handleSubmit}>
        <div className="campo">
          <label htmlFor="prov-code">Código</label>
          <select
            id="prov-code"
            value={form.code}
            onChange={(e) => setForm((f) => ({ ...f, code: e.target.value as LlmProvider["code"] }))}
          >
            {CODE_OPTIONS.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="prov-kind">Tipo de adaptador</label>
          <select
            id="prov-kind"
            value={form.kind}
            onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value as LlmProvider["kind"] }))}
          >
            {KIND_OPTIONS.map((k) => (
              <option key={k} value={k}>{k}</option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="prov-url">Base URL</label>
          <input
            id="prov-url"
            type="text"
            value={form.base_url}
            onChange={(e) => setForm((f) => ({ ...f, base_url: e.target.value }))}
          />
        </div>
        <div className="campo">
          <label htmlFor="prov-model">Modelo</label>
          <input
            id="prov-model"
            type="text"
            value={form.model}
            onChange={(e) => setForm((f) => ({ ...f, model: e.target.value }))}
          />
        </div>
        <div className="campo">
          <label htmlFor="prov-key">API key</label>
          <input
            id="prov-key"
            type="password"
            required
            value={form.api_key}
            onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
          />
        </div>
        {error && <p className="error-texto">{error}</p>}
        <button type="submit" className="boton boton-primario" disabled={crearMutacion.isPending}>
          {crearMutacion.isPending ? "Guardando…" : "Agregar proveedor"}
        </button>
      </form>

      {isLoading && <p>Cargando proveedores…</p>}

      {data && (
        <div className={styles.lista}>
          {data.map((p) => (
            <div key={p.id} className={`${styles.filaItem} tarjeta`}>
              <div className={styles.filaInfo}>
                <h3>
                  {p.code} {p.is_default && <span className={styles.estadoBadge + " " + styles.estadoReady}>Predeterminado</span>}
                </h3>
                <div className={styles.filaMeta}>
                  <span>{p.model}</span>
                  <span>{p.base_url}</span>
                  {resultados[p.id] && <span>{resultados[p.id]}</span>}
                </div>
              </div>
              <div className={styles.filaAcciones}>
                <button type="button" className="boton boton-secundario" onClick={() => testMutacion.mutate(p.id)}>
                  Probar
                </button>
                <button type="button" className="boton boton-secundario" onClick={() => toggleMutacion.mutate(p)}>
                  {p.enabled ? "Deshabilitar" : "Habilitar"}
                </button>
                {!p.is_default && (
                  <button type="button" className="boton boton-secundario" onClick={() => defaultMutacion.mutate(p)}>
                    Hacer predeterminado
                  </button>
                )}
                <button type="button" className="boton boton-secundario" onClick={() => eliminarMutacion.mutate(p.id)}>
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
