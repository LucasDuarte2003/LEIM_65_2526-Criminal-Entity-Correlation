import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./static/css/index.css";
import App from "./app.jsx";

// Aplica o tema antes do render para evitar flash
const savedTheme = localStorage.getItem("cec-theme") || "dark";
document.documentElement.dataset.theme = savedTheme;

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element '#root' was not found.");
}

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);