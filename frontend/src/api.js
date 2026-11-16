import { idToken } from "./auth";

async function call(path, options = {}) {
  const token = await idToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const r = await fetch(path, { ...options, headers });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

// /api/chat/stream: one JSON object per line; onEvent gets each (stage, delta, rewrite),
// and the final "done" object is returned (an "error" line is thrown).
async function chatStream(message, conversationId, mode, documents, onEvent) {
  const token = await idToken();
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const r = await fetch("/api/chat/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ message, conversation_id: conversationId, mode, documents }),
  });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let nl;
    while ((nl = buffer.indexOf("\n")) >= 0) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (!line) continue;
      const e = JSON.parse(line);
      if (e.type === "done") return e;
      if (e.type === "error") throw new Error(`${e.error} (${e.request_id})`);
      onEvent(e);
    }
  }
  throw new Error("응답이 중간에 끊겼습니다");
}

export const api = {
  chatStream,
  chat: (message, conversationId, mode, documents) =>
    call("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId, mode, documents }),
    }),
  library: () => call("/api/library"),
  me: () => call("/api/me"),
  logs: (preset, minutes, requestId) =>
    call(`/api/logs/${preset}?minutes=${minutes}&request_id=${encodeURIComponent(requestId || "")}`),
  conversations: () => call("/api/conversations"),
  conversation: (id) => call(`/api/conversations/${id}`),
  documents: () => call("/api/documents"),
  upload: (files) => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    return call("/api/documents", { method: "POST", body: form });
  },
  source: (chunkId) => call(`/api/source/${encodeURIComponent(chunkId)}`),
};
