import styles from "./Dictamen.module.css";

/** Barra de balance de una parte, de -100 (perjudicada) a +100 (favorecida). */
export function BalanceBar({ balance }: { balance: number }) {
  const clamped = Math.min(Math.max(balance, -100), 100);
  const anchoPorcentaje = Math.abs(clamped) / 2; // mitad del ancho total = 100
  const esFavor = clamped >= 0;

  return (
    <div className={styles.balanceBar} aria-hidden="true">
      <div className={styles.balanceEje} />
      <div
        className={`${styles.balanceRelleno} ${esFavor ? styles.balanceFavor : styles.balanceContra}`}
        style={{
          width: `${anchoPorcentaje}%`,
          left: esFavor ? "50%" : `${50 - anchoPorcentaje}%`
        }}
      />
    </div>
  );
}
