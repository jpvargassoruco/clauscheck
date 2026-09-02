import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";

/** Aplica el tema elegido (claro/oscuro/sistema) como atributo en <html>. */
export function useThemeSync() {
  const theme = useAuthStore((s) => s.theme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") {
      root.removeAttribute("data-theme");
    } else {
      root.setAttribute("data-theme", theme);
    }
  }, [theme]);
}
