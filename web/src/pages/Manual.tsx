import { Link } from "react-router-dom";
import { SiteHeader } from "@/components/Layout/SiteHeader";
import { SiteFooter } from "@/components/Layout/SiteFooter";
import { NIVEL_LABEL, NIVEL_COLOR } from "@/types/dictamen";
import styles from "./Manual.module.css";

const capitulos = [
  { id: "problema", num: "01", titulo: "Qué problema resuelve" },
  { id: "uso", num: "02", titulo: "Cómo se usa" },
  { id: "lectura", num: "03", titulo: "Cómo leer el informe" },
  { id: "escala", num: "04", titulo: "La escala de riesgo" },
  { id: "corpus", num: "05", titulo: "Los contratos incluidos" },
  { id: "normativa", num: "06", titulo: "En qué se apoya" },
  { id: "privacidad", num: "07", titulo: "Privacidad" },
  { id: "alcance", num: "08", titulo: "Alcance y límites" },
  { id: "faq", num: "09", titulo: "Preguntas frecuentes" }
];

const niveles: Array<{ nivel: keyof typeof NIVEL_LABEL; texto: string }> = [
  {
    nivel: "critico",
    texto:
      "Nulidad, inoponibilidad frente a terceros o renuncia de derechos irrenunciables. Compromete la operación completa."
  },
  {
    nivel: "alto",
    texto:
      "Desequilibrio grave o cláusula con fuerte carácter leonino: concentra las ventajas en quien redactó."
  },
  {
    nivel: "medio",
    texto:
      "Ambigüedad que la otra parte puede explotar, o carga desproporcionada pero subsanable."
  },
  {
    nivel: "bajo",
    texto: "Defecto menor de técnica contractual. No compromete la validez."
  },
  {
    nivel: "informativo",
    texto:
      "Cláusula conforme a derecho. Se documenta el contraste: en un informe serio importa tanto señalar lo defectuoso como acreditar lo correcto."
  }
];

export default function Manual() {
  return (
    <>
      <SiteHeader />
      <main className={styles.manual}>
        <div className="contenedor">
          <header className={styles.cabecera}>
            <span style={{ color: "var(--color-primario)", fontWeight: 700, fontSize: "0.8rem", textTransform: "uppercase" }}>
              Manual
            </span>
            <h1>Manual de ClausCheck</h1>
            <p style={{ maxWidth: 680, color: "var(--color-texto-suave)", fontSize: "1.05rem" }}>
              ClausCheck revisa un contrato cláusula por cláusula, señala
              cuáles están mal redactadas o desequilibradas, y dice con
              nombre y apellido a qué parte benefician y a cuál perjudican,
              citando la norma boliviana que lo sostiene.
            </p>
            <div className={styles.metaTabla}>
              <div className={`${styles.metaItem} tarjeta`}>
                <span className={styles.metaEtiqueta}>Versión</span>
                1.0.0
              </div>
              <div className={`${styles.metaItem} tarjeta`}>
                <span className={styles.metaEtiqueta}>Plataforma</span>
                Web (PWA instalable)
              </div>
              <div className={`${styles.metaItem} tarjeta`}>
                <span className={styles.metaEtiqueta}>Conexión</span>
                Requerida para analizar
              </div>
              <div className={`${styles.metaItem} tarjeta`}>
                <span className={styles.metaEtiqueta}>Jurisdicción</span>
                Bolivia
              </div>
            </div>
          </header>

          <nav className={`${styles.tocGrid} tarjeta`} aria-label="Contenido del manual">
            {capitulos.map((c) => (
              <a key={c.id} href={`#${c.id}`}>
                {c.num} · {c.titulo}
              </a>
            ))}
          </nav>

          <section id="problema" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>01</span> Qué problema resuelve</h2>
            <p>
              En Bolivia, la mayoría de los contratos que firma una persona
              común —trabajo, alquiler, anticrético, préstamo,
              compraventa— se redactan sobre plantillas reutilizadas que
              nadie vuelve a revisar. El resultado es predecible: cláusulas
              que trasladan todo el riesgo a una sola parte, renuncias de
              derechos que la ley no permite, plazos contradictorios y,
              sobre todo, omisiones.
            </p>
            <p>
              Lo que más daño hace no suele ser lo que el contrato dice,
              sino lo que calla. Un contrato de anticrético que no menciona
              cuándo se devuelve el capital. Un contrato de trabajo que no
              nombra la seguridad social. Una compraventa en la que el
              precio quedó escrito de forma ininteligible. Son defectos que
              solo se descubren cuando ya hay conflicto.
            </p>
            <p>
              ClausCheck existe para adelantar ese descubrimiento. Toma un
              contrato, lo separa en cláusulas y contrasta cada una contra
              el Código Civil, la Constitución y la normativa laboral
              vigente. Devuelve un informe de revisión asistida escrito en
              el lenguaje de un informe legal, no en el de una aplicación.
            </p>
            <h3 style={{ marginTop: 24 }}>Para quién es</h3>
            <ul>
              <li><strong>Despachos jurídicos.</strong> Una primera lectura estructurada antes de que el abogado dedique horas al documento.</li>
              <li><strong>Startups y empresas.</strong> Revisión previa de los contratos que se firman a diario, sin abrir un expediente por cada uno.</li>
              <li><strong>Personas que van a firmar.</strong> Entender qué se está aceptando antes de poner la firma, no después.</li>
            </ul>
          </section>

          <section id="uso" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>02</span> Cómo se usa</h2>
            <p>
              El recorrido completo, desde que se sube el contrato hasta
              que se tiene el informe en la mano, toma minutos.
            </p>
            <ol>
              <li><strong>Abrir Documentos.</strong> La pestaña Documentos de la app muestra los contratos ya cargados por la organización. Se puede buscar por parte, tipo de contrato o texto de cualquier cláusula.</li>
              <li><strong>Cargar el contrato.</strong> Con «Subir documento» se ofrece tomar el archivo del equipo (PDF, imagen, DOCX o TXT) o pegar el texto directamente.</li>
              <li><strong>Revisar el documento.</strong> Antes de analizar, la ficha del contrato —plaza, fecha, cuantía, forma instrumental—, los intervinientes con una marca sobre quién redactó el clausulado, y el articulado completo quedan disponibles para revisión.</li>
              <li><strong>Ejecutar el análisis.</strong> Desde la pestaña Análisis, el botón «Analizar» encola el contrato. El motor recorre siete etapas visibles: normaliza el texto, separa las cláusulas, identifica a las partes, detecta patrones de riesgo, contrasta contra la norma, pondera el impacto sobre cada parte y redacta el informe.</li>
              <li><strong>Leer y compartir.</strong> El informe queda guardado en el historial de la organización. Con «Copiar informe completo» se lleva al portapapeles en texto plano, listo para pegarlo en un correo o un mensaje.</li>
            </ol>
          </section>

          <section id="lectura" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>03</span> Cómo leer el informe</h2>
            <p>El informe se lee de arriba abajo y va de lo general a lo particular. Estas son sus seis partes.</p>
            <ul>
              <li><strong>Encabezado — Índice de riesgo.</strong> Un número de 0 a 100 que resume el estado del contrato completo, con el recuento de hallazgos, de omisiones y el grado de confianza del motor. Es el dato que se mira primero.</li>
              <li><strong>Conclusión — Síntesis ejecutiva.</strong> Un párrafo que dice qué es este contrato y cuál es su problema principal.</li>
              <li><strong>Reparto de cargas — A quién beneficia.</strong> Cada parte recibe un balance de −100 a +100 y el conteo de cláusulas a favor y en contra, con una lectura de su posición real.</li>
              <li><strong>Detalle — Hallazgos.</strong> El cuerpo del informe, ordenado por gravedad. Cada hallazgo cita el fragmento textual del contrato, explica el fundamento jurídico, reproduce el artículo aplicable y propone una redacción sustitutiva.</li>
              <li><strong>Lo que el contrato calla — Omisiones.</strong> Los puntos que este tipo de contrato debía regular y que el instrumento no contempla.</li>
              <li><strong>Plan de acción — Recomendaciones.</strong> Qué hacer, en orden de prioridad, desde la corrección de una cláusula hasta trámites concretos.</li>
            </ul>
            <div className={styles.aviso}>
              <strong>Un detalle que conviene mirar.</strong> En la ficha de
              intervinientes, la parte que redactó el clausulado aparece
              marcada. No es un dato menor: el Art. 518 del Código Civil
              establece que, en caso de duda, las cláusulas se interpretan
              en contra de quien las redactó. Saber quién escribió el
              contrato cambia cómo se lee cada ambigüedad.
            </div>
          </section>

          <section id="escala" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>04</span> La escala de riesgo</h2>
            <p>Cada hallazgo se clasifica en uno de cinco niveles. La escala no depende solo del color: el rótulo acompaña siempre al matiz.</p>
            <table className={styles.escalaTabla}>
              <thead>
                <tr><th>Nivel</th><th>Qué significa</th></tr>
              </thead>
              <tbody>
                {niveles.map((n) => (
                  <tr key={n.nivel}>
                    <td className={styles.nivelCelda} style={{ color: NIVEL_COLOR[n.nivel] }}>
                      {NIVEL_LABEL[n.nivel]}
                    </td>
                    <td>{n.texto}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={{ marginTop: 16 }}>
              El índice del documento no es un promedio. Un solo hallazgo
              crítico eleva el índice aunque el resto del clausulado sea
              intachable, porque una sola nulidad basta para comprometer el
              contrato entero.
            </p>
          </section>

          <section id="corpus" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>05</span> Los contratos incluidos</h2>
            <p>
              La plataforma incluye un corpus público de contratos reales
              de la práctica jurídica cruceña y cochabambina, digitalizados
              y separados cláusula por cláusula, disponible sin necesidad
              de cuenta en la sección{" "}
              <Link to="/#ejemplos">Ejemplos</Link>. Los números de
              documento de identidad están truncados y los nombres
              abreviados; la redacción de las cláusulas se conserva
              literal, incluidos sus errores. Cada organización, además,
              construye su propio corpus privado a medida que sube sus
              contratos.
            </p>
            <p>
              Tres ejemplos de lo que encuentra: un anticrético firmado
              como minuta privada cuando el Art. 491.3 y el Art. 1430
              exigen documento público; una transferencia de motocicleta
              con una cláusula que «descarta cualquier situación de estafa
              o estelionato», nula por mandato expreso del Art. 628.II; y
              un contrato de servicios inmobiliarios donde rechazar una
              oferta obliga a pagar la comisión íntegra, una cláusula penal
              sujeta a reducción judicial por el Art. 535.
            </p>
          </section>

          <section id="normativa" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>06</span> En qué se apoya</h2>
            <p>
              Cada cita del informe reproduce el texto oficial del
              artículo, no una paráfrasis, para que quien conozca la
              materia pueda contrastarla de inmediato. El catálogo se
              verifica contra el texto publicado de cada cuerpo legal antes
              de mostrarse.
            </p>
            <div className={styles.normativaLista}>
              <div className="tarjeta" style={{ padding: 16 }}>
                <strong>Código Civil · D.L. 12760 de 6 de agosto de 1975</strong>
                Arts. 29 · 409 · 412 · 414 · 450 · 452 · 454 · 485 · 489 · 491 · 518 · 519 · 520 · 532 · 535 · 549 · 554 · 561 · 568 · 581 · 584 · 614 · 624 · 628 · 685 · 700 · 705 · 719 · 720 · 726 · 732 · 1360 · 1429 · 1430 · 1435 · 1538
              </div>
              <div className="tarjeta" style={{ padding: 16 }}>
                <strong>Constitución Política del Estado</strong>
                Arts. 21.2 · 48.II · 48.III y IV · 56 · 115.II · 116.II · 119.II · 130
              </div>
              <div className="tarjeta" style={{ padding: 16 }}>
                <strong>Normativa laboral y especial</strong>
                Ley General del Trabajo, Arts. 16 y 46 · D.S. 110/2009 · Ley 065/2010 de Pensiones · Código de Seguridad Social y D.S. 21637 · D.S. 3150/1952 y D.S. 17288/1980 · D.S. 5383/2025 · Ley 045/2010 · Ley 16998/1979
              </div>
            </div>
          </section>

          <section id="privacidad" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>07</span> Privacidad</h2>
            <p>
              ClausCheck funciona como plataforma web instalable (PWA):
              no requiere descargar una app de una tienda y puede añadirse
              a la pantalla de inicio del equipo o del teléfono.
            </p>
            <p>
              A diferencia de una app local, los documentos se almacenan
              en la plataforma y se envían al proveedor de IA configurado
              para su análisis. Cada organización tiene sus datos aislados
              (todo documento y análisis lleva su identificador de
              organización) y el gestor documental interno nunca se
              expone directamente al usuario final. Las claves de los
              proveedores de IA se guardan cifradas y solo el personal
              autorizado de administración puede configurarlas.
            </p>
            <p>
              Los últimos informes consultados quedan disponibles para
              lectura sin conexión gracias al caché de la aplicación, pero
              generar un análisis nuevo sí requiere conexión, porque el
              texto del contrato debe procesarse contra el proveedor de IA
              configurado y contra el catálogo normativo de la base de
              datos.
            </p>
          </section>

          <section id="alcance" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>08</span> Alcance y límites</h2>
            <div className={styles.aviso}>
              <strong>Léase antes de usar el informe.</strong> ClausCheck
              es una herramienta de apoyo a la revisión contractual. No
              sustituye el criterio de un abogado habilitado ni constituye
              asesoramiento legal para un caso concreto. El informe
              señala dónde mirar y con qué norma contrastar; la decisión
              sobre qué hacer con un contrato concreto, en una situación
              concreta y frente a una contraparte concreta, sigue
              correspondiendo a un profesional del derecho. Está prevista,
              como función futura, la posibilidad de que un abogado
              habilitado revise, edite y firme este informe —con nombre,
              matrícula y fecha— para que recién entonces adquiera el
              carácter de dictamen jurídico en el sentido de la Ley 387.
            </div>
            <h3 style={{ marginTop: 24 }}>Qué hace y qué no hace</h3>
            <ul>
              <li><strong>Analiza los documentos de su organización.</strong> El corpus privado crece con cada contrato cargado, y el corpus público cubre los tipos contractuales más frecuentes de la práctica boliviana.</li>
              <li><strong>Cita normativa boliviana vigente.</strong> Las referencias corresponden al ordenamiento del Estado Plurinacional de Bolivia y no son trasladables a otra jurisdicción.</li>
              <li><strong>No litiga ni redacta por usted.</strong> Las recomendaciones proponen redacciones sustitutivas y trámites, pero requieren revisión profesional antes de incorporarse a un documento que se vaya a firmar.</li>
              <li><strong>No conoce el contexto del caso.</strong> Un contrato desequilibrado puede ser perfectamente aceptable si las partes lo negociaron con información y asesoría. El informe valora el texto, no la negociación que lo produjo.</li>
            </ul>
          </section>

          <section id="faq" className={styles.capitulo}>
            <h2><span className={styles.capituloNumero}>09</span> Preguntas frecuentes</h2>
            <dl className={styles.faq}>
              <dt>¿Necesito internet para usarla?</dt>
              <dd>
                Para analizar un contrato nuevo, sí: el texto se procesa
                contra el proveedor de IA configurado y contra el
                catálogo normativo de la base de datos. Los informes ya
                generados quedan disponibles para lectura sin conexión
                gracias al caché de la PWA.
              </dd>
              <dt>¿Qué pasa con los datos de mis clientes?</dt>
              <dd>
                Se almacenan en la plataforma, aislados por organización.
                El gestor documental interno nunca se expone directamente
                al usuario final, y cada consulta pasa por control de
                membresía de la organización.
              </dd>
              <dt>¿Puedo confiar en las citas legales?</dt>
              <dd>
                Cada artículo reproduce el texto oficial del cuerpo legal
                correspondiente, verificado contra la publicación del
                Código Civil, la Constitución y la normativa laboral. Un
                verificador automático descarta cualquier cita que no
                exista en la base de datos antes de mostrar el informe.
              </dd>
              <dt>¿Un índice de 100 significa que el contrato es inválido?</dt>
              <dd>
                No. Significa que el documento acumula defectos graves,
                entre ellos al menos uno que compromete su validez o su
                oponibilidad frente a terceros. La declaración de nulidad
                corresponde a un juez; el índice solo ordena la urgencia
                de la revisión.
              </dd>
              <dt>¿Puedo compartir un informe?</dt>
              <dd>
                Sí. El botón «Copiar informe completo» lo lleva al
                portapapeles en texto plano —con hallazgos, citas, normas
                y recomendaciones— listo para pegarlo en un correo o un
                mensaje.
              </dd>
              <dt>¿Se pueden añadir otros contratos?</dt>
              <dd>
                Sí. Cada organización sube sus propios contratos desde
                Documentos, y el corpus público y el catálogo normativo
                crecen de forma independiente. Incorporar un nuevo tipo
                contractual al catálogo es trabajo de análisis jurídico y
                carga de datos por parte del equipo de administración.
              </dd>
            </dl>
          </section>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
