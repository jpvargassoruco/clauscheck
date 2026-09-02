import { useAuthStore } from "@/store/auth";

export function ThemeToggle() {
  const theme = useAuthStore((s) => s.theme);
  const setTheme = useAuthStore((s) => s.setTheme);

  function alternar() {
    const orden: (typeof theme)[] = ["system", "light", "dark"];
    const idx = orden.indexOf(theme);
    setTheme(orden[(idx + 1) % orden.length]);
  }

  const etiqueta =
    theme === "system" ? "Sistema" : theme === "light" ? "Claro" : "Oscuro";
  const icono = theme === "system" ? "🖥️" : theme === "light" ? "☀️" : "🌙";

  return (
    <button
      type="button"
      className="boton boton-secundario"
      onClick={alternar}
      aria-label={`Tema: ${etiqueta}. Cambiar tema`}
      title={`Tema: ${etiqueta}`}
    >
      <span aria-hidden="true">{icono}</span>
      <span className="visualmente-oculto">{etiqueta}</span>
    </button>
  );
}
