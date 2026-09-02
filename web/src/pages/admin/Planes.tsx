import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/api/client";
import type { Plan } from "@/types/domain";
import styles from "../app/AppPages.module.css";

export default function Planes() {
  const queryClient = useQueryClient();
  const [editando, setEditando] = useState<Plan | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-plans"],
    queryFn: adminApi.plans.list
  });

  const actualizarMutacion = useMutation({
    mutationFn: (plan: Plan) =>
      adminApi.plans.update(plan.code, {
        nombre: plan.nombre,
        analisis_mes: plan.analisis_mes,
        docs_max: plan.docs_max,
        precio_bob: plan.precio_bob
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-plans"] });
      setEditando(null);
    }
  });

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Planes</h1>
          <p>Límites y precios de cada plan de suscripción.</p>
        </div>
      </div>

      {isLoading && <p>Cargando planes…</p>}

      {data && (
        <table className={styles.tabla}>
          <thead>
            <tr>
              <th>Código</th>
              <th>Nombre</th>
              <th>Análisis/mes</th>
              <th>Docs. máx.</th>
              <th>Precio (Bs)</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.map((p) => {
              const filaEditable = editando?.code === p.code ? editando : p;
              const enEdicion = editando?.code === p.code;
              return (
                <tr key={p.code}>
                  <td>{p.code}</td>
                  <td>
                    {enEdicion ? (
                      <input
                        type="text"
                        value={filaEditable.nombre}
                        onChange={(e) => setEditando({ ...filaEditable, nombre: e.target.value })}
                      />
                    ) : (
                      p.nombre
                    )}
                  </td>
                  <td>
                    {enEdicion ? (
                      <input
                        type="number"
                        value={filaEditable.analisis_mes}
                        onChange={(e) =>
                          setEditando({ ...filaEditable, analisis_mes: Number(e.target.value) })
                        }
                      />
                    ) : (
                      p.analisis_mes
                    )}
                  </td>
                  <td>
                    {enEdicion ? (
                      <input
                        type="number"
                        value={filaEditable.docs_max}
                        onChange={(e) =>
                          setEditando({ ...filaEditable, docs_max: Number(e.target.value) })
                        }
                      />
                    ) : (
                      p.docs_max
                    )}
                  </td>
                  <td>
                    {enEdicion ? (
                      <input
                        type="number"
                        value={filaEditable.precio_bob}
                        onChange={(e) =>
                          setEditando({ ...filaEditable, precio_bob: Number(e.target.value) })
                        }
                      />
                    ) : (
                      p.precio_bob
                    )}
                  </td>
                  <td>
                    {enEdicion ? (
                      <button
                        type="button"
                        className="boton boton-primario"
                        onClick={() => actualizarMutacion.mutate(filaEditable)}
                      >
                        Guardar
                      </button>
                    ) : (
                      <button type="button" className="boton boton-secundario" onClick={() => setEditando(p)}>
                        Editar
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
