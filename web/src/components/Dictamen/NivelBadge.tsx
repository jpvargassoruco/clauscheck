import { NIVEL_COLOR, NIVEL_LABEL, type Nivel } from "@/types/dictamen";
import styles from "./Dictamen.module.css";

export function NivelBadge({ nivel }: { nivel: Nivel }) {
  return (
    <span
      className={styles.nivelBadge}
      style={{ backgroundColor: `${NIVEL_COLOR[nivel]}1f`, color: NIVEL_COLOR[nivel] }}
    >
      <span
        className={styles.nivelPunto}
        style={{ backgroundColor: NIVEL_COLOR[nivel] }}
        aria-hidden="true"
      />
      {NIVEL_LABEL[nivel]}
    </span>
  );
}
