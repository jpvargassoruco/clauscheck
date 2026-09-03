import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ApiError, adminApi } from "@/api/client";
import styles from "../app/AppPages.module.css";

function mesActualISO(): string {
  const hoy = new Date();
  return `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}`;
}

/** "YYYY-MM" -> {desde, hasta} en YYYY-MM-DD (primer y último día del mes). */
function rangoDelMes(mes: string): { desde: string; hasta: string } {
  const [anioStr, mesStr] = mes.split("-");
  const anio = Number(anioStr);
  const m = Number(mesStr);
  const desde = `${anio}-${String(m).padStart(2, "0")}-01`;
  const ultimoDia = new Date(anio, m, 0).getDate();
  const hasta = `${anio}-${String(m).padStart(2, "0")}-${String(ultimoDia).padStart(2, "0")}`;
  return { desde, hasta };
}

function formatoUsd(v: number): string {
  return `USD ${v.toFixed(2)}`;
}

function formatoBs(v: number): string {
  return `Bs ${v.toFixed(2)}`;
}

function BarraUso({ usado, total }: { usado: number; total: number }) {
  const pct = total > 0 ? Math.min(100, Math.round((usado / total) * 100)) : 0;
  const alerta = pct >= 80;
  return (
    <div className={styles.barraMiniFila}>
      <span className={styles.barraMiniTexto}>
        {usado.toLocaleString("es-BO")} / {total.toLocaleString("es-BO")} ({pct}%)
      </span>
      <div className={styles.barraMini}>
        <div
          className={`${styles.barraMiniRelleno} ${alerta ? styles.barraMiniAlerta : ""}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function GraficoDiario({
  serie
}: {
  serie: { fecha: string; analisis: number; palabras: number; costo_usd: number }[];
}) {
  if (serie.length === 0) {
    return <p style={{ margin: 0, color: "var(--color-texto-suave)" }}>Sin análisis en el rango seleccionado.</p>;
  }

  const ancho = Math.max(480, serie.length * 40);
  const alto = 160;
  const margenInferior = 28;
  const max = Math.max(1, ...serie.map((d) => d.analisis));
  const anchoBarra = (ancho / serie.length) * 0.6;

  return (
    <div className={styles.graficoDiarioSvgWrap}>
      <svg width={ancho} height={alto} role="img" aria-label="Análisis por día">
        {serie.map((d, i) => {
          const x = (ancho / serie.length) * i + (ancho / serie.length - anchoBarra) / 2;
          const alturaBarra = ((alto - margenInferior) * d.analisis) / max;
          const y = alto - margenInferior - alturaBarra;
          return (
            <g key={d.fecha}>
              <title>
                {d.fecha}: {d.analisis} análisis, {d.palabras.toLocaleString("es-BO")} palabras,{" "}
                {formatoUsd(d.costo_usd)}
              </title>
              <rect
                x={x}
                y={y}
                width={anchoBarra}
                height={Math.max(alturaBarra, 1)}
                fill="var(--color-primario)"
                rx={2}
              />
              <text
                x={x + anchoBarra / 2}
                y={alto - 8}
                textAnchor="middle"
                fontSize="9"
                fill="var(--color-texto-suave)"
              >
                {d.fecha.slice(5)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function Consumo() {
  const [mes, setMes] = useState(mesActualISO());
  const [orgId, setOrgId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);

  const { desde, hasta } = useMemo(() => rangoDelMes(mes), [mes]);

  const { data: orgs } = useQuery({ queryKey: ["admin-orgs"], queryFn: adminApi.orgs.list });

  const { data, isLoading } = useQuery({
    queryKey: ["admin-consumo", desde, hasta, orgId],
    queryFn: () => adminApi.consumo.get({ desde, hasta, org_id: orgId || undefined })
  });

  async function handleExportar() {
    setError(null);
    setDescargando(true);
    try {
      await adminApi.consumo.exportCsv({ desde, hasta, org_id: orgId || undefined });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "No se pudo descargar el CSV.");
    } finally {
      setDescargando(false);
    }
  }

  return (
    <div className={styles.pagina}>
      <div className={styles.cabecera}>
        <div>
          <h1>Consumo</h1>
          <p>Análisis, palabras, tokens y costo por organización.</p>
        </div>
      </div>

      <div className={`${styles.filtros} tarjeta`} style={{ padding: 16 }}>
        <div className="campo">
          <label htmlFor="consumo-mes">Mes</label>
          <input
            id="consumo-mes"
            type="month"
            value={mes}
            onChange={(e) => setMes(e.target.value)}
          />
        </div>
        <div className="campo">
          <label htmlFor="consumo-org">Organización</label>
          <select id="consumo-org" value={orgId} onChange={(e) => setOrgId(e.target.value)}>
            <option value="">Todas</option>
            {orgs?.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nombre}
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          className="boton boton-secundario"
          onClick={handleExportar}
          disabled={descargando}
        >
          {descargando ? "Descargando…" : "Descargar CSV"}
        </button>
      </div>

      {error && <p className="error-texto">{error}</p>}
      {isLoading && <p>Cargando consumo…</p>}

      {data && (
        <>
          <div className={styles.tilesGrid}>
            <div className={`${styles.tile} tarjeta`}>
              <p className={styles.tileLabel}>Análisis</p>
              <p className={styles.tileValor}>{data.totales.analisis.toLocaleString("es-BO")}</p>
            </div>
            <div className={`${styles.tile} tarjeta`}>
              <p className={styles.tileLabel}>Palabras</p>
              <p className={styles.tileValor}>{data.totales.palabras.toLocaleString("es-BO")}</p>
            </div>
            <div className={`${styles.tile} tarjeta`}>
              <p className={styles.tileLabel}>Tokens (in/out)</p>
              <p className={styles.tileValor} style={{ fontSize: "1.1rem" }}>
                {data.totales.tokens_in.toLocaleString("es-BO")} /{" "}
                {data.totales.tokens_out.toLocaleString("es-BO")}
              </p>
            </div>
            <div className={`${styles.tile} tarjeta`}>
              <p className={styles.tileLabel}>Costo</p>
              <p className={styles.tileValor} style={{ fontSize: "1.1rem" }}>
                {formatoUsd(data.totales.costo_usd)}
              </p>
              <p style={{ margin: 0, fontSize: "0.85rem", color: "var(--color-texto-suave)" }}>
                {formatoBs(data.totales.costo_bs)} (1 USD = {data.usd_bob} Bs)
              </p>
            </div>
          </div>

          <div className={`${styles.graficoDiario} tarjeta`}>
            <h3 style={{ marginTop: 0 }}>Análisis por día</h3>
            <GraficoDiario serie={data.serie_diaria} />
          </div>

          <div style={{ overflowX: "auto" }}>
            <table className={styles.tabla}>
              <thead>
                <tr>
                  <th>Organización</th>
                  <th>Plan</th>
                  <th>Análisis (rango)</th>
                  <th>Palabras (rango)</th>
                  <th>Análisis / mes actual</th>
                  <th>Palabras / mes actual</th>
                  <th>Tokens in/out</th>
                  <th>Costo USD</th>
                  <th>Costo Bs</th>
                </tr>
              </thead>
              <tbody>
                {data.rows.length === 0 && (
                  <tr>
                    <td colSpan={9} style={{ color: "var(--color-texto-suave)" }}>
                      Sin datos en el rango seleccionado.
                    </td>
                  </tr>
                )}
                {data.rows.map((r) => (
                  <tr key={r.org_id}>
                    <td>{r.org_nombre}</td>
                    <td>{r.plan_code}</td>
                    <td>{r.analisis}</td>
                    <td>{r.palabras.toLocaleString("es-BO")}</td>
                    <td>
                      <BarraUso usado={r.analisis_mes_usado} total={r.analisis_mes_plan} />
                    </td>
                    <td>
                      <BarraUso usado={r.palabras_mes_usado} total={r.palabras_mes_plan} />
                    </td>
                    <td>
                      {r.tokens_in.toLocaleString("es-BO")} / {r.tokens_out.toLocaleString("es-BO")}
                    </td>
                    <td>{formatoUsd(r.costo_usd)}</td>
                    <td>{formatoBs(r.costo_bs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
