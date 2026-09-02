import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, ApiError } from "@/api/client";
import type { AccessRequest, AccessRequestStatusValue, Role } from "@/types/domain";
import styles from "../app/AppPages.module.css";

const ESTADOS: { value: AccessRequestStatusValue | ""; label: string }[] = [
  { value: "pending", label: "Pendientes" },
  { value: "approved", label: "Aprobadas" },
  { value: "rejected", label: "Rechazadas" },
  { value: "", label: "Todas" }
];

const ROLES: Role[] = ["owner", "admin", "member"];

export default function Solicitudes() {
  const queryClient = useQueryClient();
  const [filtro, setFiltro] = useState<AccessRequestStatusValue | "">("pending");
  const [aprobando, setAprobando] = useState<AccessRequest | null>(null);
  const [rechazando, setRechazando] = useState<AccessRequest | null>(null);
  const [planCode, setPlanCode] = useState("free");
  const [role, setRole] = useState<Role>("owner");
  const [motivo, setMotivo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-access-requests", filtro],
    queryFn: () => adminApi.accessRequests.list(filtro || undefined)
  });

  const { data: planes } = useQuery({
    queryKey: ["admin-plans"],
    queryFn: adminApi.plans.list
  });

  const aprobarMutacion = useMutation({
    mutationFn: (input: { id: string; plan_code: string; role: Role }) =>
      adminApi.accessRequests.approve(input.id, { plan_code: input.plan_code, role: input.role }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-access-requests"] });
      setAprobando(null);
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.detail : "No se pudo aprobar la solicitud.")
  });

  const rechazarMutacion = useMutation({
    mutationFn: (input: { id: string; motivo: string }) =>
      adminApi.accessRequests.reject(input.id, input.motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-access-requests"] });
      setRechazando(null);
      setMotivo("");
    },
    onError: (err) =>
      setError(err instanceof ApiError ? err.detail : "No se pudo rechazar la solicitud.")
  });

  function badgeClass(status: AccessRequestStatusValue) {
    if (status === "approved") return `${styles.estadoBadge} ${styles.estadoReady}`;
    if (status === "rejected") return `${styles.estadoBadge} ${styles.estadoFailed}`;
    return `${styles.estadoBadge} ${styles.estadoPending}`;
  }

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Solicitudes de acceso</h1>
          <p>Solicitudes recibidas desde el formulario público «Solicitar acceso».</p>
        </div>
      </div>

      <div className={styles.filtros}>
        <div className="campo">
          <label htmlFor="filtro-estado">Estado</label>
          <select
            id="filtro-estado"
            value={filtro}
            onChange={(e) => setFiltro(e.target.value as AccessRequestStatusValue | "")}
          >
            {ESTADOS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <p className="error-texto">{error}</p>}
      {isLoading && <p>Cargando solicitudes…</p>}
      {data && data.length === 0 && <p className={styles.vacio}>No hay solicitudes en este estado.</p>}

      {data && data.length > 0 && (
        <div className={styles.lista}>
          {data.map((r) => (
            <div key={r.id} className={`${styles.filaItem} tarjeta`} style={{ flexDirection: "column", alignItems: "stretch" }}>
              <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 12 }}>
                <div className={styles.filaInfo}>
                  <h3>
                    {r.nombre} — {r.organizacion}
                  </h3>
                  <div className={styles.filaMeta}>
                    <span>{r.email}</span>
                    {r.telefono && <span>{r.telefono}</span>}
                    <span>{new Date(r.created_at).toLocaleString("es-BO")}</span>
                    <span className={badgeClass(r.status)}>{r.status}</span>
                  </div>
                  {r.motivo && <p style={{ margin: "6px 0 0" }}>{r.motivo}</p>}
                </div>
                {r.status === "pending" && (
                  <div className={styles.filaAcciones}>
                    <button
                      type="button"
                      className="boton boton-primario"
                      onClick={() => {
                        setAprobando(r);
                        setRechazando(null);
                        setError(null);
                      }}
                    >
                      Aprobar
                    </button>
                    <button
                      type="button"
                      className="boton boton-secundario"
                      onClick={() => {
                        setRechazando(r);
                        setAprobando(null);
                        setError(null);
                      }}
                    >
                      Rechazar
                    </button>
                  </div>
                )}
              </div>

              {aprobando?.id === r.id && (
                <div
                  style={{
                    display: "flex",
                    gap: 10,
                    flexWrap: "wrap",
                    alignItems: "flex-end",
                    marginTop: 12,
                    borderTop: "1px solid var(--color-borde)",
                    paddingTop: 12
                  }}
                >
                  <div className="campo">
                    <label htmlFor={`plan-${r.id}`}>Plan</label>
                    <select
                      id={`plan-${r.id}`}
                      value={planCode}
                      onChange={(e) => setPlanCode(e.target.value)}
                    >
                      {(planes ?? []).map((p) => (
                        <option key={p.code} value={p.code}>
                          {p.nombre}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="campo">
                    <label htmlFor={`role-${r.id}`}>Rol</label>
                    <select
                      id={`role-${r.id}`}
                      value={role}
                      onChange={(e) => setRole(e.target.value as Role)}
                    >
                      {ROLES.map((rl) => (
                        <option key={rl} value={rl}>
                          {rl}
                        </option>
                      ))}
                    </select>
                  </div>
                  <button
                    type="button"
                    className="boton boton-primario"
                    disabled={aprobarMutacion.isPending}
                    onClick={() => aprobarMutacion.mutate({ id: r.id, plan_code: planCode, role })}
                  >
                    {aprobarMutacion.isPending ? "Aprobando…" : "Confirmar aprobación"}
                  </button>
                  <button type="button" className="boton boton-secundario" onClick={() => setAprobando(null)}>
                    Cancelar
                  </button>
                </div>
              )}

              {rechazando?.id === r.id && (
                <div
                  style={{
                    display: "flex",
                    gap: 10,
                    flexWrap: "wrap",
                    alignItems: "flex-end",
                    marginTop: 12,
                    borderTop: "1px solid var(--color-borde)",
                    paddingTop: 12
                  }}
                >
                  <div className="campo" style={{ flex: 1, minWidth: 220 }}>
                    <label htmlFor={`motivo-${r.id}`}>Motivo del rechazo</label>
                    <input
                      id={`motivo-${r.id}`}
                      type="text"
                      value={motivo}
                      onChange={(e) => setMotivo(e.target.value)}
                    />
                  </div>
                  <button
                    type="button"
                    className="boton boton-primario"
                    disabled={rechazarMutacion.isPending}
                    onClick={() => rechazarMutacion.mutate({ id: r.id, motivo })}
                  >
                    {rechazarMutacion.isPending ? "Rechazando…" : "Confirmar rechazo"}
                  </button>
                  <button type="button" className="boton boton-secundario" onClick={() => setRechazando(null)}>
                    Cancelar
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
