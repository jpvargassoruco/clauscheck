import { SiteHeader } from "@/components/Layout/SiteHeader";
import { SiteFooter } from "@/components/Layout/SiteFooter";
import { Hero } from "./sections/Hero";
import { Problema } from "./sections/Problema";
import { Solucion } from "./sections/Solucion";
import { ComoFunciona } from "./sections/ComoFunciona";
import { Ejemplos } from "./sections/Ejemplos";
import { Planes } from "./sections/Planes";
import { Equipo } from "./sections/Equipo";
import { Contacto } from "./sections/Contacto";

export default function Landing() {
  return (
    <>
      <SiteHeader />
      <main>
        <Hero />
        <Problema />
        <Solucion />
        <ComoFunciona />
        <Ejemplos />
        <Planes />
        <Equipo />
        <Contacto />
      </main>
      <SiteFooter />
    </>
  );
}
