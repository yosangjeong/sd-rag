import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { initAuth } from "./auth";
import "./style.css";

const root = createRoot(document.getElementById("root"));

// sign-in could not start (config.json unreachable, Cognito down): say so, never a blank page
function AuthError({ message }) {
  return (
    <div className="empty" role="alert">
      <h1>로그인을 준비하지 못했습니다</h1>
      <p>{message}</p>
      <button className="button" onClick={() => window.location.replace("/")}>다시 시도</button>
    </div>
  );
}

initAuth()
  .then((user) => root.render(<App user={user} />))
  .catch((err) => {
    console.error(err);
    if (window.location.search) window.history.replaceState({}, "", "/");
    root.render(<AuthError message={String(err?.message || err)} />);
  });
