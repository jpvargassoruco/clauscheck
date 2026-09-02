import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { publicApi } from "@/api/client";
import { SiteHeader } from "@/components/Layout/SiteHeader";
import { SiteFooter } from "@/components/Layout/SiteFooter";
import { Dictamen } from "@/components/Dictamen/Dictamen";

export default function Ejemplo() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["public-corpus-item", id],
    queryFn: () => publicApi.corpusItem(id as string),
    enabled: Boolean(id)
  });

  return (
    <>
      <SiteHeader />
      <main className="contenedor" style={{ padding: "48px 24px" }}>
        <p style={{ marginBottom: 24 }}>
          <Link to="/#ejemplos">← Volver a ejemplos</Link>
        </p>

        {isLoading && <p>Cargando informe…</p>}
        {isError && <p>No se pudo cargar este ejemplo.</p>}

        {data && (
          <>
            <header style={{ marginBottom: 24 }}>
              <h1>{data.document.titulo}</h1>
              <p style={{ color: "var(--color-texto-suave)" }}>
                {data.document.ficha.tipo_contrato} · {data.document.ficha.plaza} ·{" "}
                {data.document.ficha.fecha} · {data.document.ficha.cuantia}
              </p>
            </header>
            {data.dictamen ? (
              <Dictamen dictamen={data.dictamen} tituloDocumento={data.document.titulo} />
            ) : (
              <p>Este documento todavía no tiene un informe publicado.</p>
            )}
          </>
        )}
      </main>
      <SiteFooter />
    </>
  );
}
