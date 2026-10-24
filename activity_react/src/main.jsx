import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { initTheme } from "./ThemeToggle";
import { ConfirmProvider } from "./Confirm";
import "./index.css";
import App from "./App.jsx";

initTheme();

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <ConfirmProvider>
      <App />
    </ConfirmProvider>
  </StrictMode>
);
