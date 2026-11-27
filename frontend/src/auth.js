// Sign-in with the Cognito managed login page (OpenID Connect, authorization code +
// PKCE, done by oidc-client-ts). The ID token goes to the API as a Bearer token; the
// API verifies it (backend/src/sdrag/api/auth.py).
// Settings come from /config.json, written at deploy time (infra), so the same build
// works in any environment. Without it (local development) sign-in is skipped and the
// API runs with auth_mode=dev.
import { UserManager, WebStorageStateStore } from "oidc-client-ts";

let manager = null;

export async function initAuth() {
  // only "no config.json" (404, or the dev server) means local mode; a network error
  // or a 5xx must not render the page signed-out, so it is thrown (main.jsx shows it)
  const r = await fetch("/config.json").catch(() => null);
  if (!r) throw new Error("설정을 불러오지 못했습니다 (네트워크 오류)");
  if (r.status === 404 || (import.meta.env.DEV && !r.ok)) return null; // local: no sign-in
  if (!r.ok) throw new Error(`설정을 불러오지 못했습니다 (${r.status})`);
  // the dev server answers a missing file with index.html: not JSON, local mode
  const cfg = await r.json().catch(() => null);
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
    try {
      await manager.signinRedirectCallback();
    } catch (err) {
      // a stale or mismatched ?code= (reload, back button, another tab): drop it and
      // sign in again below instead of failing the whole page
      console.warn("sign-in callback failed", err);
      await manager.removeUser().catch(() => {});
    }
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
  let user = await manager.getUser();
  if (!user || user.expired) {
    // the tab slept past the token's hour: renew quietly, else sign in again
    user = await manager.signinSilent().catch(() => null);
    if (!user) {
      await manager.signinRedirect();
      return new Promise(() => {}); // the page is leaving
    }
  }
  return user.id_token;
}

export async function signOut() {
  if (!manager) return;
  await manager.removeUser();
  window.location.href = manager.logoutUrl;
}
