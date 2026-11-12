import { idToken } from "./auth";

async function call(path, options = {}) {
  const token = await idToken();
  const headers = { ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const r = await fetch(path, { ...options, headers });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export const api = {
  chat: (message, conversationId, mode, documents) =>
    call("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId, mode, documents }),
    }),
  library: () => call("/api/library"),
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
