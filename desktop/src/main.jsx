import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
// Note: the UI prefers the "Geist" typeface (see tailwind.config.js) but
// gracefully falls back to the system font, so no font package is required.
// To bundle the real Geist font, run:
//   npm install @fontsource-variable/geist @fontsource-variable/geist-mono
// then add: import "@fontsource-variable/geist"; import "@fontsource-variable/geist-mono";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
