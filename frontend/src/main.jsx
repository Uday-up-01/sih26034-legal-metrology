import React from "react";
import ReactDOM from "react-dom/client";

import InspectorPage from "./pages/InspectorPage";

import "./styles.css";

ReactDOM.createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>
    <InspectorPage />
  </React.StrictMode>
);