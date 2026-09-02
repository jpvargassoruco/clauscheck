import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/api/client";
import styles from "../app/AppPages.module.css";

const PLAN_OPTIONS = ["free", "pro", "despacho"];

export default function Organizaciones() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["admin-orgs"],
    queryFn: adminApi.orgs.list
  });

  const cambiarPlanMutacion = useMutation({
    mutationFn: (input: { id: string; plan: string }) =>
      adminApi.orgs.updatePlan(input.id, input.plan),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-orgs"] })
  });

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Organizaciones</h1>
          <p>Todas las organizaciones registradas en la plataforma.</p>
        </div>
      </div>

      {isLoading && <p>Cargando organizaciones…</p>}

      {data && (
        <table className={styles.tabla}>
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Slug</th>
              <th>Demo</th>
              <th>Plan</th>
            </tr>
          </thead>
          <tbody>
            {data.map((org) => (
              <tr key={org.id}>
                <td>{org.nombre}</td>
                <td>{org.slug}</td>
                <td>{org.is_demo ? "Sí" : "No"}</td>
                <td>
                  <select
                    value={org.plan_code}
                    onChange={(e) =>
                      cambiarPlanMutacion.mutate({ id: org.id, plan: e.target.value })
                    }
                  >
                    {PLAN_OPTIONS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
