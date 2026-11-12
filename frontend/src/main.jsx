import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { initAuth } from "./auth";
import "./style.css";

initAuth().then((user) => {
  createRoot(document.getElementById("root")).render(<App user={user} />);
});
