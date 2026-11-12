// Sign-in with the Cognito managed login page (OpenID Connect, authorization code +
// PKCE, done by oidc-client-ts). The ID token goes to the API as a Bearer token; the
// API verifies it (backend/src/sdrag/api/auth.py).
// Settings come from /config.json, written at deploy time (infra), so the same build
// works in any environment. Without it (local development) sign-in is skipped and the
// API runs with auth_mode=dev.
import { UserManager, WebStorageStateStore } from "oidc-client-ts";

let manager = null;

export async function initAuth() {
  const r = await fetch("/config.json").catch(() => null);
  const cfg = r && r.ok ? await r.json().catch(() => null) : null;
  if (!cfg || !cfg.authority) return null; // local: no sign-in
  manager = new UserManager({
    authority: cfg.authority, // https://cognito-idp.<region>.amazonaws.com/<pool id>
    client_id: cfg.clientId,
    redirect_uri: window.location.origin + "/",
    post_logout_redirect_uri: window.location.origin + "/",
    response_type: "code",
    scope: "openid email",
    userStore: new WebStorageStateStore({ store: window.sessionStorage }),
  });
  manager.logoutUrl = `${cfg.domain}/logout?client_id=${cfg.clientId}&logout_uri=${encodeURIComponent(window.location.origin + "/")}`;
  if (window.location.search.includes("code=")) {
    await manager.signinRedirectCallback();
    window.history.replaceState({}, "", "/");
  }
  const user = await manager.getUser();
  if (!user || user.expired) {
    await manager.signinRedirect();
    return new Promise(() => {}); // the page is leaving
  }
  return user;
}

export async function idToken() {
  if (!manager) return null;
  const user = await manager.getUser();
  return user ? user.id_token : null;
}

export async function signOut() {
  if (!manager) return;
  await manager.removeUser();
  window.location.href = manager.logoutUrl;
}
