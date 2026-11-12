// One page: conversations on the left, the chat in the middle, the cited source on
// the right; uploads at the top of the left column.
import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { signOut } from "./auth";
import Answer, { Sources } from "./Answer";
import Logs from "./Logs";

function where(c) {
  const page = c.page_start ? ` p.${c.page_start}${c.page_end && c.page_end !== c.page_start ? `-${c.page_end}` : ""}` : "";
  return `${c.title} › ${c.heading || ""}${page}`;
}

const STATUS = { queued: "대기", processing: "처리 중", retrying: "재시도 대기", done: "완료", failed: "실패" };

function Uploads({ onAsk }) {
  const [docs, setDocs] = useState([]);
  const [busy, setBusy] = useState(false);
  const input = useRef();
  const [open, setOpen] = useState(false);
  const refresh = () => api.documents().then(setDocs).catch(() => {});
  const working = docs.some((d) => ["queued", "processing", "retrying"].includes(d.status));
  useEffect(() => {
    refresh();
    // poll fast while files are being processed, slowly otherwise
    const t = setInterval(refresh, working ? 3000 : 15000);
    return () => clearInterval(t);
  }, [working]);
  const send = async (files) => {
    if (!files.length) return;
    setBusy(true);
    try {
      const r = await api.upload(files);
      if (r.rejected.length) alert(r.rejected.map((x) => `${x.file}: ${x.reason}`).join("\n"));
      setOpen(true); // show the list so the progress is visible
    } finally {
      setBusy(false);
      input.current.value = "";
      refresh();
    }
  };
  const done = docs.filter((d) => d.status === "done").length;
  return (
    <section className="uploads">
      <label className="button upload">
        {busy ? "올리는 중…" : "문서 올리기"}
        <small>PDF · DOCX · HWPX, 여러 개 가능</small>
        <input ref={input} type="file" multiple accept=".pdf,.docx,.hwpx" hidden
               onChange={(e) => send([...e.target.files])} />
      </label>
      {docs.length > 0 && (
        <details open={open} onToggle={(e) => setOpen(e.target.open)}>
          <summary>내 문서 {done}/{docs.length} 처리됨{working ? " · 처리 중…" : ""}</summary>
          <ul>
            {docs.map((d) => (
              <li key={d.id} className={d.status}>
                <span className="file">{d.file}</span>
                <small>
                  {STATUS[d.status] || d.status}
                  {d.stage ? ` · ${d.stage}` : ""}
                  {d.chunks ? ` · ${d.chunks}조각` : ""}
                  {d.status === "failed" && d.error ? ` · ${d.error}` : ""}
                </small>
                {d.status === "done" && d.doc && (
                  <button className="link ask" onClick={() => onAsk(d.doc, d.file)}>이 문서에 질문</button>
                )}
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
  const [library, setLibrary] = useState([]);
  const [scope, setScope] = useState(""); // "": every document; otherwise one document id
  const [evaluator, setEvaluator] = useState(false);
  const [view, setView] = useState("chat"); // chat | logs

  const loadConvs = () => api.conversations().then(setConvs).catch(() => {});
  useEffect(() => { loadConvs(); api.me().then((m) => setEvaluator(m.evaluator)).catch(() => {}); }, []);
  useEffect(() => {
    const load = () => api.library().then(setLibrary).catch(() => {});
    load();
    const t = setInterval(load, 30000); // new uploads appear once indexed
    return () => clearInterval(t);
  }, []);

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
      const r = await api.chat(q, convId, mode, scope ? [scope] : []);
      setConvId(r.conversation_id);
      setMessages((m) => [...m, { role: "assistant", text: r.answer, citations: r.citations, mode: r.mode,
                                  latency_ms: r.latency_ms, steps: r.steps,
                                  searched: r.searched !== q ? r.searched : null }]);
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
        {evaluator && (
          <button className="link" onClick={() => setView(view === "logs" ? "chat" : "logs")}>
            {view === "logs" ? "← 채팅으로" : "로그 보기 (평가자)"}
          </button>
        )}
        <Uploads onAsk={(id) => { setScope(id); setConvId(null); setMessages([]); setSource(null);
                                  api.library().then(setLibrary).catch(() => {});
                                  setTimeout(() => document.querySelector(".ask input")?.focus(), 0); }} />
        <button className="button" onClick={() => { setConvId(null); setMessages([]); setSource(null); }}>
          새 대화
        </button>
        <ul className="convs">
          {convs.map((c) => (
            <li key={c.id} className={c.id === convId ? "active" : ""} onClick={() => open(c.id)}>{c.title}</li>
          ))}
        </ul>
      </aside>

      {view === "logs" ? <main className="chat"><Logs /></main> : (
      <main className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <p className="hint">한국·미국 노동법 문서와 올린 문서를 근거로 답합니다. 한국어나 영어로 물어보세요.</p>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.role === "assistant" ? (
                <>
                  <Answer text={m.text} citations={m.citations || []} onOpen={openSource} label={where} />
                  {(m.citations || []).length > 0 && (
                    <Sources citations={m.citations} onOpen={openSource} label={where} />
                  )}
                  {m.searched && <small className="meta">검색한 질문: {m.searched}<br /></small>}
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
          <select value={scope} onChange={(e) => setScope(e.target.value)} title="검색 범위" className="scope">
            <option value="">모든 문서</option>
            <optgroup label="내 문서">
              {library.filter((d) => d.mine).map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
            </optgroup>
            <optgroup label="공용 문서">
              {library.filter((d) => !d.mine).map((d) => <option key={d.id} value={d.id}>{d.title}</option>)}
            </optgroup>
          </select>
          <input value={text} onChange={(e) => setText(e.target.value)} placeholder="질문을 입력하세요" maxLength={2000} />
          <button className="button" disabled={pending}>보내기</button>
        </form>
      </main>
      )}

      {view === "chat" && source && (
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
