// Composition root: the only file allowed to import infrastructure/.
// Step 09 adds the GatewayProvider and picks Fake or Http gateways here.
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { App } from "./presentation/App";

const root = document.getElementById("root");
if (!root) throw new Error("#root element missing");

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
