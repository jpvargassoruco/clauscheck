import { Navigate, Route, Routes } from "react-router-dom";
import { useThemeSync } from "@/hooks/useThemeSync";
import { RequireAuth, RequireSuperadmin } from "@/components/Layout/RequireAuth";
import { AppShell } from "@/components/Layout/AppShell";
import { AdminShell } from "@/components/Layout/AdminShell";

import Landing from "@/pages/landing/Landing";
import Ejemplo from "@/pages/landing/Ejemplo";
import Manual from "@/pages/Manual";
import Login from "@/pages/auth/Login";
import Registro from "@/pages/auth/Registro";

import Documentos from "@/pages/app/Documentos";
import Analisis from "@/pages/app/Analisis";
import AnalisisDetalle from "@/pages/app/AnalisisDetalle";
import Historial from "@/pages/app/Historial";
import Ajustes from "@/pages/app/Ajustes";

import Proveedores from "@/pages/admin/Proveedores";
import Normativa from "@/pages/admin/Normativa";
import Organizaciones from "@/pages/admin/Organizaciones";
import Planes from "@/pages/admin/Planes";

export default function App() {
  useThemeSync();

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/ejemplos/:id" element={<Ejemplo />} />
      <Route path="/manual" element={<Manual />} />
      <Route path="/login" element={<Login />} />
      <Route path="/registro" element={<Registro />} />

      <Route element={<RequireAuth />}>
        <Route path="/app" element={<AppShell />}>
          <Route index element={<Navigate to="documentos" replace />} />
          <Route path="documentos" element={<Documentos />} />
          <Route path="analisis" element={<Analisis />} />
          <Route path="analisis/:id" element={<AnalisisDetalle />} />
          <Route path="historial" element={<Historial />} />
          <Route path="ajustes" element={<Ajustes />} />
        </Route>
      </Route>

      <Route element={<RequireSuperadmin />}>
        <Route path="/admin" element={<AdminShell />}>
          <Route index element={<Navigate to="proveedores" replace />} />
          <Route path="proveedores" element={<Proveedores />} />
          <Route path="normativa" element={<Normativa />} />
          <Route path="organizaciones" element={<Organizaciones />} />
          <Route path="planes" element={<Planes />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
