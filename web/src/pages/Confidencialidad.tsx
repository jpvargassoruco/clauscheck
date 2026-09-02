import { SiteHeader } from "@/components/Layout/SiteHeader";
import { SiteFooter } from "@/components/Layout/SiteFooter";
import styles from "./Confidencialidad.module.css";

export default function Confidencialidad() {
  return (
    <>
      <SiteHeader />
      <main className={styles.pagina}>
        <div className="contenedor">
          <header className={styles.cabecera}>
            <span style={{ color: "var(--color-primario)", fontWeight: 700, fontSize: "0.8rem", textTransform: "uppercase" }}>
              Confidencialidad
            </span>
            <h1>Cómo se tratan sus documentos</h1>
          </header>

          <div className={styles.contenido}>
            <p>
              Los documentos que se suben a ClausCheck se almacenan en la
              plataforma, en infraestructura ubicada en Bolivia (nube de
              COTAS), aislados por organización. Al ejecutar un análisis,
              antes de enviar el texto de cada cláusula al proveedor de
              inteligencia artificial configurado, el sistema seudonimiza
              los datos identificatorios que reconoce en el texto —nombres,
              números de cédula de identidad, NIT y números de cuenta— para
              reducir lo que sale del entorno de la organización. El
              proveedor de IA utilizado se configura por organización desde
              el panel de administración y puede cambiarse en cualquier
              momento; hoy incluye Anthropic (Claude) y proveedores
              compatibles con la API de OpenAI, según la clave que cada
              organización registre.
            </p>
            <p>
              Los documentos y los informes generados se conservan mientras
              la organización mantenga la cuenta activa, y se eliminan a
              pedido, conforme al derecho a la protección de datos
              personales reconocido en el artículo 130 de la Constitución
              Política del Estado (acción de protección de privacidad).
              ClausCheck no utiliza los documentos ni los informes de sus
              clientes para entrenar modelos de inteligencia artificial, ni
              propios ni de terceros.
            </p>
          </div>
        </div>
      </main>
      <SiteFooter />
    </>
  );
}
