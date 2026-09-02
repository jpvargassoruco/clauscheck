import styles from "../Landing.module.css";

const puntos = [
  {
    titulo: "Plantillas que nadie revisa",
    texto:
      "La mayoría de los contratos que firma una persona común —trabajo, alquiler, anticrético, préstamo, compraventa— se redactan sobre plantillas reutilizadas que nadie vuelve a revisar."
  },
  {
    titulo: "Lo que calla, no lo que dice",
    texto:
      "Lo que más daño hace no suele ser lo que el contrato dice, sino lo que omite: un anticrético que no dice cuándo se devuelve el capital, un contrato de trabajo sin seguridad social."
  },
  {
    titulo: "Gestión documental física",
    texto:
      "En Bolivia, y particularmente en Santa Cruz, la gestión documental sigue siendo predominantemente física y manual, lo que aumenta la vulnerabilidad frente a errores humanos y pérdida de información."
  },
  {
    titulo: "Se descubre tarde",
    texto:
      "Son defectos que solo se descubren cuando ya hay conflicto: el desequilibrio contractual llega a juicio en lugar de corregirse antes de la firma."
  }
];

export function Problema() {
  return (
    <section id="problema" className={styles.seccion}>
      <div className="contenedor">
        <span className={styles.seccionEtiqueta}>El problema</span>
        <h2 className={styles.seccionTitulo}>
          Los contratos que se firman a diario esconden riesgos que nadie
          detecta a tiempo
        </h2>
        <p className={styles.seccionIntro}>
          ¿Cómo puede una aplicación basada en inteligencia artificial
          contribuir a la detección automática de cláusulas abusivas en
          contratos laborales, comerciales y financieros, mejorando la
          seguridad jurídica y optimizando la gestión documental en
          despachos, startups y empresas?
        </p>
        <div className={styles.problemaGrid}>
          {puntos.map((p) => (
            <div key={p.titulo} className={`${styles.problemaTarjeta} tarjeta`}>
              <h3>{p.titulo}</h3>
              <p>{p.texto}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
