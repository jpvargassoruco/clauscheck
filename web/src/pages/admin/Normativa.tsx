import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, ApiError } from "@/api/client";
import type { Articulo } from "@/types/domain";
import styles from "../app/AppPages.module.css";

export default function Normativa() {
  const queryClient = useQueryClient();
  const [cuerpo, setCuerpo] = useState("");
  const [numero, setNumero] = useState("");
  const [q, setQ] = useState("");
  const [editando, setEditando] = useState<Articulo | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: cuerpos } = useQuery({
    queryKey: ["admin-cuerpos"],
    queryFn: adminApi.normativa.cuerpos
  });

  const { data: articulos, isLoading } = useQuery({
    queryKey: ["admin-articulos", cuerpo, numero, q],
    queryFn: () => adminApi.normativa.articulos({ cuerpo, numero, q })
  });

  const actualizarMutacion = useMutation({
    // PATCH /admin/normativa/articulos/{id} valida el artículo completo
    // (schemas.ArticuloIn), no un parche parcial: hay que reenviar todos
    // los campos, no sólo los que cambiaron en el formulario.
    mutationFn: (input: Articulo) =>
      adminApi.normativa.updateArticulo(input.id, {
        cuerpo_id: input.cuerpo_id,
        numero: input.numero,
        inciso: input.inciso,
        titulo: input.titulo,
        texto: input.texto,
        vigente: input.vigente,
        verificado: input.verificado,
        fuente_url: input.fuente_url
      } satisfies Omit<Articulo, "id" | "version">),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-articulos"] });
      setEditando(null);
    }
  });

  const importarMutacion = useMutation({
    mutationFn: (file: File) => adminApi.normativa.importJson(file),
    onSuccess: (res) => {
      setMensaje(
        `Importados ${res.cuerpos_creados} cuerpos nuevos (${res.cuerpos_actualizados} actualizados) ` +
          `y ${res.articulos_creados} artículos nuevos (${res.articulos_actualizados} actualizados).`
      );
      queryClient.invalidateQueries({ queryKey: ["admin-cuerpos"] });
      queryClient.invalidateQueries({ queryKey: ["admin-articulos"] });
    },
    onError: (err) =>
      setMensaje(err instanceof ApiError ? err.detail : "No se pudo importar el archivo.")
  });

  const reembedMutacion = useMutation({
    mutationFn: adminApi.normativa.reembed,
    onSuccess: (res) => setMensaje(`Reembedding aplicado a ${res.reembedded} artículos.`)
  });

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Normativa</h1>
          <p>Cuerpos legales y artículos verificados que respaldan los dictámenes.</p>
        </div>
        <div className={styles.filaAcciones}>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) importarMutacion.mutate(file);
            }}
          />
          <button
            type="button"
            className="boton boton-secundario"
            onClick={() => fileInputRef.current?.click()}
            disabled={importarMutacion.isPending}
          >
            {importarMutacion.isPending ? "Importando…" : "Importar JSON"}
          </button>
          <button
            type="button"
            className="boton boton-secundario"
            onClick={() => reembedMutacion.mutate()}
            disabled={reembedMutacion.isPending}
          >
            Reembeder
          </button>
        </div>
      </div>

      {mensaje && <p>{mensaje}</p>}

      <div className="tarjeta" style={{ padding: 16 }}>
        <h3 style={{ marginTop: 0 }}>Cuerpos legales</h3>
        <div className={styles.filaMeta}>
          {cuerpos?.map((c) => (
            <span key={c.id}>{c.code} — {c.nombre}</span>
          ))}
        </div>
      </div>

      <div className={styles.filtros}>
        <div className="campo">
          <label htmlFor="filtro-cuerpo">Cuerpo</label>
          <select id="filtro-cuerpo" value={cuerpo} onChange={(e) => setCuerpo(e.target.value)}>
            <option value="">Todos</option>
            {cuerpos?.map((c) => (
              <option key={c.id} value={c.code}>{c.code}</option>
            ))}
          </select>
        </div>
        <div className="campo">
          <label htmlFor="filtro-numero">Número</label>
          <input id="filtro-numero" type="text" value={numero} onChange={(e) => setNumero(e.target.value)} />
        </div>
        <div className="campo">
          <label htmlFor="filtro-q">Buscar texto</label>
          <input id="filtro-q" type="text" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      {isLoading && <p>Cargando artículos…</p>}

      {articulos && (
        <table className={styles.tabla}>
          <thead>
            <tr>
              <th>Número</th>
              <th>Título</th>
              <th>Texto</th>
              <th>Verificado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {articulos.map((a) => (
              <tr key={a.id}>
                <td>{a.numero}{a.inciso ? `.${a.inciso}` : ""}</td>
                <td>{a.titulo ?? "—"}</td>
                <td style={{ maxWidth: 360 }}>
                  {editando?.id === a.id ? (
                    <textarea
                      rows={3}
                      value={editando.texto}
                      onChange={(e) => setEditando({ ...editando, texto: e.target.value })}
                      style={{ width: "100%" }}
                    />
                  ) : (
                    a.texto.slice(0, 140) + (a.texto.length > 140 ? "…" : "")
                  )}
                </td>
                <td>
                  {editando?.id === a.id ? (
                    <input
                      type="checkbox"
                      checked={editando.verificado}
                      onChange={(e) => setEditando({ ...editando, verificado: e.target.checked })}
                    />
                  ) : a.verificado ? (
                    "Sí"
                  ) : (
                    "No"
                  )}
                </td>
                <td>
                  {editando?.id === a.id ? (
                    <button
                      type="button"
                      className="boton boton-primario"
                      onClick={() => actualizarMutacion.mutate(editando)}
                    >
                      Guardar
                    </button>
                  ) : (
                    <button type="button" className="boton boton-secundario" onClick={() => setEditando(a)}>
                      Editar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
