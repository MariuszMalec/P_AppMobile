import { useEffect, useState } from "react";

const KEY = "theme";

export function initTheme() {
  let t = null;
  try { t = localStorage.getItem(KEY); } catch { /* brak dostępu */ }
  if (t !== "light" && t !== "dark") {
    t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.documentElement.dataset.theme = t;
  return t;
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(
    () => document.documentElement.dataset.theme || "light"
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(KEY, theme); } catch { /* ignoruj */ }
  }, [theme]);

  const dark = theme === "dark";
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={() => setTheme(dark ? "light" : "dark")}
      aria-label={dark ? "Włącz tryb jasny" : "Włącz tryb ciemny"}
      title={dark ? "Tryb jasny" : "Tryb ciemny"}
    >
      {dark ? "☀️" : "🌙"}
    </button>
  );
}
