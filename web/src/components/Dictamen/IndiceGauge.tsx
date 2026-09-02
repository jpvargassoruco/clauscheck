import { NIVEL_COLOR, type Nivel } from "@/types/dictamen";
import styles from "./Dictamen.module.css";

const RADIO = 54;
const CIRCUNFERENCIA = 2 * Math.PI * RADIO;

export function IndiceGauge({
  indice,
  nivel
}: {
  indice: number;
  nivel: Nivel;
}) {
  const fraccion = Math.min(Math.max(indice, 0), 100) / 100;
  const offset = CIRCUNFERENCIA * (1 - fraccion);
  const color = NIVEL_COLOR[nivel];

  return (
    <div
      className={styles.gauge}
      role="img"
      aria-label={`Índice de riesgo ${indice} de 100`}
    >
      <svg viewBox="0 0 120 120" width="120" height="120">
        <circle
          cx="60"
          cy="60"
          r={RADIO}
          fill="none"
          stroke="var(--color-borde)"
          strokeWidth="12"
        />
        <circle
          cx="60"
          cy="60"
          r={RADIO}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={CIRCUNFERENCIA}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
        />
      </svg>
      <div className={styles.gaugeCentro}>
        <span className={styles.gaugeNumero}>{indice}</span>
        <span className={styles.gaugeEscala}>/100</span>
      </div>
    </div>
  );
}
