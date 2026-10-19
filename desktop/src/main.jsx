import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
// Bundled typefaces (work offline; no network fonts in the packaged app).
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";

// Let CSS adapt to the platform (e.g. macOS vibrancy for the sidebar).
const platform = (typeof window !== "undefined" && window.api?.platform) || "web";
document.documentElement.classList.add(`platform-${platform}`);

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
