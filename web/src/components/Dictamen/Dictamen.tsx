import { useState } from "react";
import { NIVEL_ORDEN, type Dictamen as DictamenT } from "@/types/dictamen";
import { dictamenATexto } from "@/lib/dictamenText";
import { NivelBadge } from "./NivelBadge";
import { IndiceGauge } from "./IndiceGauge";
import { BalanceBar } from "./BalanceBar";
import styles from "./Dictamen.module.css";

interface DictamenProps {
  dictamen: DictamenT;
  tituloDocumento?: string;
}

export function Dictamen({ dictamen: d, tituloDocumento }: DictamenProps) {
  const [copiado, setCopiado] = useState(false);

  const hallazgosOrdenados = [...d.hallazgos].sort(
    (a, b) => NIVEL_ORDEN.indexOf(a.nivel) - NIVEL_ORDEN.indexOf(b.nivel)
  );
  const omisionesOrdenadas = [...d.omisiones].sort(
    (a, b) => NIVEL_ORDEN.indexOf(a.nivel) - NIVEL_ORDEN.indexOf(b.nivel)
  );
  const recomendacionesOrdenadas = [...d.recomendaciones].sort(
    (a, b) => a.prioridad - b.prioridad
  );

  async function copiar() {
    const texto = dictamenATexto(d, tituloDocumento);
    try {
      await navigator.clipboard.writeText(texto);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    } catch {
      // Sin permisos de portapapeles: no interrumpir el flujo.
    }
  }

  return (
    <article className={styles.dictamen}>
      <header className={`${styles.encabezado} tarjeta`}>
        <IndiceGauge indice={d.indice_riesgo} nivel={d.nivel} />
        <div className={styles.encabezadoInfo}>
          <NivelBadge nivel={d.nivel} />
          <dl className={styles.encabezadoMetricas}>
            <div>
              <dt>Confianza</dt>
              <dd>{Math.round(d.confianza * 100)}%</dd>
            </div>
            <div>
              <dt>Hallazgos</dt>
              <dd>{d.resumen.hallazgos}</dd>
            </div>
            <div>
              <dt>Omisiones</dt>
              <dd>{d.resumen.omisiones}</dd>
            </div>
          </dl>
        </div>
        <button
          type="button"
          className="boton boton-secundario"
          onClick={copiar}
        >
          {copiado ? "Copiado ✓" : "Copiar dictamen completo"}
        </button>
      </header>

      <section className={styles.seccion}>
        <h2>Síntesis</h2>
        <p className={styles.sintesis}>{d.sintesis}</p>
      </section>

      <section className={styles.seccion}>
        <h2>Reparto de cargas</h2>
        <p className="visualmente-oculto">
          Balance de cada parte, de -100 (totalmente perjudicada) a +100
          (totalmente favorecida).
        </p>
        <ul className={styles.listaPartes}>
          {d.partes.map((p) => (
            <li key={p.id} className={`${styles.parteItem} tarjeta`}>
              <div className={styles.parteCabecera}>
                <span className={styles.parteNombre}>
                  {p.nombre}
                  {p.redacto && (
                    <span
                      className={styles.redactoMarca}
                      title="Redactó el clausulado. Art. 518 del Código Civil: en caso de duda, las cláusulas se interpretan en contra de quien las redactó."
                    >
                      redactó ⓘ
                    </span>
                  )}
                </span>
                <span className={styles.parteRol}>{p.rol}</span>
              </div>
              <BalanceBar balance={p.balance} />
              <div className={styles.parteConteo}>
                <span>{p.balance > 0 ? "+" : ""}{p.balance}</span>
                <span>{p.a_favor} a favor · {p.en_contra} en contra</span>
              </div>
              <p className={styles.parteLectura}>{p.lectura}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.seccion}>
        <h2>Hallazgos</h2>
        <ul className={styles.listaHallazgos}>
          {hallazgosOrdenados.map((h) => (
            <li key={h.id} className={`${styles.hallazgo} tarjeta`}>
              <div className={styles.hallazgoCabecera}>
                <NivelBadge nivel={h.nivel} />
                <h3>{h.titulo}</h3>
                <span className={styles.clausulaRef}>cláusula {h.clausula_id}</span>
              </div>
              <blockquote className={styles.cita}>“{h.cita_textual}”</blockquote>
              <p>
                <strong>Fundamento: </strong>
                {h.fundamento}
              </p>
              {h.articulos.length > 0 && (
                <ul className={styles.articulos}>
                  {h.articulos.map((a) => (
                    <li key={a.articulo_id}>
                      <strong>
                        Art. {a.numero}
                        {a.inciso ? `.${a.inciso}` : ""} {a.cuerpo}
                      </strong>
                      : {a.texto}{" "}
                      <a href={a.fuente_url} target="_blank" rel="noreferrer">
                        fuente
                      </a>
                    </li>
                  ))}
                </ul>
              )}
              <p className={styles.sustitutiva}>
                <strong>Redacción sustitutiva: </strong>
                {h.redaccion_sustitutiva}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.seccion}>
        <h2>Omisiones</h2>
        <ul className={styles.listaHallazgos}>
          {omisionesOrdenadas.map((o) => (
            <li key={o.id} className={`${styles.hallazgo} tarjeta`}>
              <div className={styles.hallazgoCabecera}>
                <NivelBadge nivel={o.nivel} />
                <h3>{o.titulo}</h3>
              </div>
              <p>{o.descripcion}</p>
              {o.articulos.length > 0 && (
                <ul className={styles.articulos}>
                  {o.articulos.map((a) => (
                    <li key={a.articulo_id}>
                      <strong>
                        Art. {a.numero}
                        {a.inciso ? `.${a.inciso}` : ""} {a.cuerpo}
                      </strong>
                      : {a.texto}{" "}
                      <a href={a.fuente_url} target="_blank" rel="noreferrer">
                        fuente
                      </a>
                    </li>
                  ))}
                </ul>
              )}
              <p className={styles.sustitutiva}>
                <strong>Recomendación: </strong>
                {o.recomendacion}
              </p>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.seccion}>
        <h2>Recomendaciones</h2>
        <ol className={styles.recomendaciones}>
          {recomendacionesOrdenadas.map((r, i) => (
            <li key={i}>
              <span className={styles.recTipo}>{r.tipo}</span>
              {r.accion}
            </li>
          ))}
        </ol>
      </section>
    </article>
  );
}
