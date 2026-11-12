// One page: conversations on the left, the chat in the middle, the cited source on
// the right; uploads at the top of the left column.
import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { signOut } from "./auth";

function where(c) {
  const page = c.page_start ? ` p.${c.page_start}${c.page_end && c.page_end !== c.page_start ? `-${c.page_end}` : ""}` : "";
  return `${c.title} › ${c.heading || ""}${page}`;
}

// "[2]" in the answer text becomes a button that opens source 2
function AnswerText({ text, citations, onOpen }) {
  const byN = Object.fromEntries(citations.map((c) => [c.n, c]));
  return (
    <p className="answer">
      {text.split(/(\[\d+\])/).map((part, i) => {
        const m = part.match(/^\[(\d+)\]$/);
        if (m && byN[m[1]]) {
          return (
            <button key={i} className="cite" title={where(byN[m[1]])} onClick={() => onOpen(byN[m[1]])}>
              {m[1]}
            </button>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}

function Uploads() {
  const [docs, setDocs] = useState([]);
  const [busy, setBusy] = useState(false);
  const input = useRef();
  const refresh = () => api.documents().then(setDocs).catch(() => {});
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 5000); // processing status
    return () => clearInterval(t);
  }, []);
  const send = async (files) => {
    if (!files.length) return;
    setBusy(true);
    try {
      const r = await api.upload(files);
      if (r.rejected.length) alert(r.rejected.map((x) => `${x.file}: ${x.reason}`).join("\n"));
    } finally {
      setBusy(false);
      input.current.value = "";
      refresh();
    }
  };
  const done = docs.filter((d) => d.status === "done").length;
  return (
    <section className="uploads">
      <label className="button">
        {busy ? "올리는 중…" : "문서 올리기 (PDF·DOCX·HWPX)"}
        <input ref={input} type="file" multiple accept=".pdf,.docx,.hwpx" hidden
               onChange={(e) => send([...e.target.files])} />
      </label>
      {docs.length > 0 && (
        <details>
          <summary>내 문서 {done}/{docs.length} 처리됨</summary>
          <ul>
            {docs.map((d) => (
              <li key={d.id} className={d.status}>
                {d.file} <small>{d.status}{d.chunks ? ` · ${d.chunks}조각` : ""}{d.error ? ` · ${d.error}` : ""}</small>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}

export default function App({ user }) {
  const [convs, setConvs] = useState([]);
  const [convId, setConvId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [mode, setMode] = useState("basic");
  const [pending, setPending] = useState(false);
  const [source, setSource] = useState(null);

  const loadConvs = () => api.conversations().then(setConvs).catch(() => {});
  useEffect(() => { loadConvs(); }, []);

  const open = async (id) => {
    setConvId(id);
    setSource(null);
    const c = await api.conversation(id);
    setMessages(c.messages);
  };
  const ask = async (e) => {
    e.preventDefault();
    const q = text.trim();
    if (!q || pending) return;
    setText("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setPending(true);
    try {
      const r = await api.chat(q, convId, mode);
      setConvId(r.conversation_id);
      setMessages((m) => [...m, { role: "assistant", text: r.answer, citations: r.citations, mode: r.mode,
                                  latency_ms: r.latency_ms, steps: r.steps }]);
      loadConvs();
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `오류: ${err.message}`, citations: [] }]);
    } finally {
      setPending(false);
    }
  };
  const openSource = async (c) => setSource({ ...c, ...(await api.source(c.chunk_id)) });

  return (
    <div className="layout">
      <aside className="side">
        <header>
          <b>노동법 문서 검색</b>
          {user && <button className="link" onClick={signOut}>로그아웃</button>}
        </header>
        <Uploads />
        <button className="button" onClick={() => { setConvId(null); setMessages([]); setSource(null); }}>
          새 대화
        </button>
        <ul className="convs">
          {convs.map((c) => (
            <li key={c.id} className={c.id === convId ? "active" : ""} onClick={() => open(c.id)}>{c.title}</li>
          ))}
        </ul>
      </aside>

      <main className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <p className="hint">한국·미국 노동법 문서와 올린 문서를 근거로 답합니다. 한국어나 영어로 물어보세요.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.role === "assistant" ? (
                <>
                  <AnswerText text={m.text} citations={m.citations || []} onOpen={openSource} />
                  {(m.citations || []).length > 0 && (
                    <ol className="sources">
                      {m.citations.map((c) => (
                        <li key={c.n} value={c.n}><button className="link" onClick={() => openSource(c)}>{where(c)}</button></li>
                      ))}
                    </ol>
                  )}
                  {m.latency_ms && <small className="meta">{m.mode === "agent" ? `에이전트 · 검색 ${m.steps.filter((s) => s.tool === "search").length}회 · ` : ""}{(m.latency_ms / 1000).toFixed(1)}초</small>}
                </>
              ) : (
                <p>{m.text}</p>
              )}
            </div>
          ))}
          {pending && <div className="msg assistant"><p className="hint">찾는 중…</p></div>}
        </div>
        <form className="ask" onSubmit={ask}>
          <select value={mode} onChange={(e) => setMode(e.target.value)} title="검색 방식">
            <option value="basic">기본 검색</option>
            <option value="agent">에이전트</option>
          </select>
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="질문을 입력하세요" maxLength={2000} />
          <button className="button" disabled={pending}>보내기</button>
        </form>
      </main>

      {source && (
        <aside className="source">
          <header>
            <b>{where(source)}</b>
            <button className="link" onClick={() => setSource(null)}>닫기</button>
          </header>
          <small>{source.doc_id} · 글자 {source.start}–{source.end}{source.ocr ? " · OCR" : ""}</small>
          <pre>{source.text}</pre>
        </aside>
      )}
    </div>
  );
}
