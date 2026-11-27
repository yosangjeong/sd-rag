// One page: conversations on the left, the chat in the middle, the cited source on
// the right; uploads at the top of the left column.
import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { signOut } from "./auth";
import Answer, { Sources } from "./Answer";
import Logs from "./Logs";
import { Badge, version } from "./versions";

function where(c) {
  const page = c.page_start ? ` p.${c.page_start}${c.page_end && c.page_end !== c.page_start ? `-${c.page_end}` : ""}` : "";
  return `${c.title} › ${version(c.heading).base}${page}`;
}

// starting points on the empty page: both languages, both fields, one cross-lingual
const EXAMPLES = [
  "수습 기간에도 해고 예고를 해야 하나요?",
  "난임치료휴가는 며칠까지 유급인가요?",
  "전세 계약이 끝났는데 보증금을 못 받으면 어떻게 하나요?",
  "How much notice must an employer give before a mass layoff?",
  "미국에서 집주인이 아이가 있다는 이유로 임대를 거절해도 되나요?",
];

// what the streaming answer is doing (api.chatStream stages)
const STAGE = {
  searching: (mode) => (mode === "agent" ? "에이전트가 검색하는 중" : "근거를 찾는 중"),
  ranking: () => "찾은 근거를 고르는 중",
  writing: () => "답을 쓰는 중",
  rewriting: () => "숫자를 출처와 맞춰 다시 쓰는 중",
};

const STATUS = { queued: "대기", processing: "처리 중", retrying: "재시도 대기", done: "완료", failed: "실패" };
const ACTIVE = ["queued", "processing", "retrying"];

// the API's reasons for refusing a file (backend/src/sdrag/api/main.py upload()), in
// Korean; an unknown reason is shown as sent
const MAX_FILES = 100;
function reasonKo(reason) {
  const r = String(reason || "");
  let m;
  if (r === "only PDF, DOCX and HWPX") return "PDF · DOCX · HWPX만 올릴 수 있습니다";
  if ((m = r.match(/^over (\d+) MB$/))) return `${m[1]} MB 초과`;
  if ((m = r.match(/^already uploaded \(as (.*)\)$/))) return `이미 올린 파일입니다 (${m[1]})`;
  if (r === "not a PDF file") return "PDF 파일이 아닙니다";
  if (r.startsWith("not a DOCX/HWPX file"))
    return "DOCX/HWPX 파일이 아닙니다 (예전 .hwp/.doc의 확장자만 바꾼 파일이면 HWPX, DOCX 또는 PDF로 저장해 주세요)";
  if (r === "could not be queued, try again") return "접수하지 못했습니다 (잠시 뒤 다시 올려 주세요)";
  if (r === "could not be saved, try again") return "저장하지 못했습니다 (잠시 뒤 다시 올려 주세요)";
  if ((m = r.match(/^daily limit of (\d+) files$/))) return `하루에 ${m[1]}개까지 올릴 수 있습니다`;
  return r;
}

function Uploads({ onAsk }) {
  const [docs, setDocs] = useState([]);
  const [busy, setBusy] = useState(false);
  const input = useRef();
  const [open, setOpen] = useState(false);
  const refresh = () => api.documents().then(setDocs).catch(() => {});
  const working = docs.some((d) => ACTIVE.includes(d.status));
  useEffect(() => {
    refresh();
    // poll fast while files are being processed, slowly otherwise
    const t = setInterval(refresh, working ? 3000 : 15000);
    return () => clearInterval(t);
  }, [working]);
  const send = async (files) => {
    if (!files.length || busy) return;
    // the API takes 1 to 100 files per request
    if (files.length > MAX_FILES) {
      alert(`한 번에 ${MAX_FILES}개까지 올릴 수 있습니다 (${files.length}개 선택됨)`);
      input.current.value = "";
      return;
    }
    // the API refuses files over 50 MB; say so before sending them
    const big = files.filter((f) => f.size > 50 * 2 ** 20);
    files = files.filter((f) => f.size <= 50 * 2 ** 20);
    if (big.length) alert(big.map((f) => `${f.name}: 50 MB 초과`).join("\n"));
    if (!files.length) { input.current.value = ""; return; }
    setBusy(true);
    try {
      // in requests of 10: one request of 100 large files could outlast CloudFront's 60 s
      const rejected = [];
      for (let i = 0; i < files.length; i += 10) {
        const r = await api.upload(files.slice(i, i + 10));
        rejected.push(...r.rejected);
        refresh();
      }
      if (rejected.length) alert(rejected.map((x) => `${x.file}: ${reasonKo(x.reason)}`).join("\n"));
      setOpen(true); // show the list so the progress is visible
    } catch (err) {
      alert(`업로드 실패: ${err.message}`);
    } finally {
      setBusy(false);
      input.current.value = "";
      refresh();
    }
  };
  const done = docs.filter((d) => d.status === "done").length;
  return (
    <section className="uploads">
      <label className={`button upload${busy ? " busy" : ""}`} aria-disabled={busy}>
        {busy ? "올리는 중…" : "문서 올리기"}
        <small>PDF · DOCX · HWPX, 여러 개 가능</small>
        <input ref={input} type="file" multiple accept=".pdf,.docx,.hwpx" hidden disabled={busy}
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
                  {ACTIVE.includes(d.status) && d.stage ? ` · ${d.stage}` : ""}
                  {d.chunks ? ` · ${d.chunks}조각` : ""}
                  {d.status === "failed" && d.error ? ` · ${d.error}` : ""}
                </small>
                {d.status === "done" && d.doc && (
                  <button className="link ask-doc" onClick={() => onAsk(d.doc, d.file)}>이 문서에 질문</button>
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
  const [draft, setDraft] = useState(null); // {stage, text} while an answer streams in
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

  const latest = useRef(null); // the conversation clicked last: a slower earlier load is dropped
  // bumped whenever the shown conversation changes (open, new, "이 문서에 질문"): an answer
  // that arrives after the user moved on is not added to the conversation now on screen
  const shown = useRef(0);
  const leave = () => { shown.current += 1; setDraft(null); };
  const open = async (id) => {
    leave();
    latest.current = id;
    setConvId(id);
    setSource(null);
    try {
      const c = await api.conversation(id);
      if (latest.current === id) setMessages(c.messages);
    } catch (err) {
      if (latest.current === id) setMessages([{ role: "assistant", text: `오류: ${err.message}`, citations: [] }]);
    }
  };
  const ask = async (e, preset) => {
    e?.preventDefault();
    const q = (preset ?? text).trim();
    if (!q || pending) return;
    setText("");
    setMessages((m) => [...m, { role: "user", text: q }]);
    setPending(true);
    setDraft({ stage: "searching", text: "" });
    const asked = shown.current; // the conversation this question belongs to
    const here = () => shown.current === asked;
    const onEvent = (e) => {
      if (!here()) return; // another conversation is on screen: no draft there
      if (e.type === "stage") setDraft((d) => ({ ...d, stage: e.stage }));
      else if (e.type === "delta") setDraft((d) => ({ ...d, text: d.text + e.text }));
      else if (e.type === "rewrite") setDraft({ stage: "rewriting", text: "" });
    };
    try {
      let r;
      try {
        r = await api.chatStream(q, convId, mode, scope ? [scope] : [], onEvent);
      } catch (err) {
        if (!String(err.message).startsWith("404") && !String(err.message).startsWith("405")) throw err;
        r = await api.chat(q, convId, mode, scope ? [scope] : []); // an API without streaming
      }
      if (!here()) { loadConvs(); return; } // the server saved the turn in its own conversation
      latest.current = r.conversation_id;
      setConvId(r.conversation_id);
      setMessages((m) => [...m, { role: "assistant", text: r.answer, citations: r.citations, mode: r.mode,
                                  unchecked_figures: r.unchecked_figures,
                                  latency_ms: r.latency_ms, steps: r.steps,
                                  searched: r.searched !== q ? r.searched : null }]);
      loadConvs();
    } catch (err) {
      if (here()) setMessages((m) => [...m, { role: "assistant", text: `오류: ${err.message}`, citations: [] }]);
      else loadConvs();
    } finally {
      setPending(false);
      if (here()) setDraft(null);
    }
  };
  const openSource = async (c) => {
    try {
      setSource({ ...c, ...(await api.source(c.chunk_id)) });
    } catch (err) {
      alert(`원문을 열지 못했습니다: ${err.message}`);
    }
  };

  return (
    <div className="layout">
      <aside className="side">
        <header className="brand">
          <div>
            <b>법령 문서 검색</b>
            <small>한국·미국 법령 + 내 문서</small>
          </div>
          {user && <button className="link" onClick={signOut}>로그아웃</button>}
        </header>
        {evaluator && (
          <button className="link" onClick={() => setView(view === "logs" ? "chat" : "logs")}>
            {view === "logs" ? "← 채팅으로" : "로그 보기 (평가자)"}
          </button>
        )}
        <Uploads onAsk={(id) => { leave(); latest.current = null; setScope(id); setConvId(null); setMessages([]); setSource(null);
                                  api.library().then(setLibrary).catch(() => {});
                                  setTimeout(() => document.querySelector(".ask input")?.focus(), 0); }} />
        <button className="button ghost" onClick={() => { leave(); latest.current = null; setConvId(null); setMessages([]); setSource(null); }}>
          + 새 대화
        </button>
        {convs.length > 0 && <div className="section-label">대화</div>}
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
            <div className="empty">
              <h1>무엇이든 물어보세요</h1>
              <p>한국·미국 법령(노동, 부동산)과 올린 문서를 근거로, 출처 위치와 함께 답합니다.
                한국어로 물어도 영어 문서를, 영어로 물어도 한국어 문서를 찾습니다.</p>
              <div className="examples">
                {EXAMPLES.map((q) => (
                  <button key={q} className="example" onClick={() => ask(null, q)}>{q}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              {m.role === "assistant" ? (
                <>
                  <Answer text={m.text} citations={m.citations || []} onOpen={openSource} label={where} />
                  {(m.unchecked_figures || []).length > 0 && (
                    <p className="figure-warn" role="note">
                      출처에서 확인되지 않은 숫자가 있습니다: <b>{m.unchecked_figures.join(", ")}</b>. 원문을 확인해 주세요.
                    </p>
                  )}
                  {(m.citations || []).length > 0 && (
                    <Sources citations={m.citations} onOpen={openSource} label={where} />
                  )}
                  <div className="meta">
                    {m.mode === "agent" && <span className="chip">에이전트 · 검색 {(m.steps || []).filter((s) => s.tool === "search").length}회</span>}
                    {m.latency_ms != null && <span className="chip">{(m.latency_ms / 1000).toFixed(1)}초</span>}
                    {m.searched && <span className="chip wide" title="앞 대화를 반영해 고친 질문">검색한 질문: {m.searched}</span>}
                  </div>
                </>
              ) : (
                <p>{m.text}</p>
              )}
            </div>
          ))}
          {pending && draft && (
            <div className="msg assistant">
              {draft?.text ? <p className="draft">{draft.text}</p> : null}
              <p className="thinking">
                <span className="dots"><i /><i /><i /></span>
                {STAGE[draft?.stage]?.(mode) || "근거를 찾고 답을 쓰는 중"}
              </p>
            </div>
          )}
        </div>
        <form className="ask" onSubmit={ask}>
          <div className="modes" role="group" aria-label="검색 방식">
            <button type="button" className={mode === "basic" ? "on" : ""} onClick={() => setMode("basic")}
                    title="번역 검색 + 재순위: 빠르고 정확">기본</button>
            <button type="button" className={mode === "agent" ? "on" : ""} onClick={() => setMode("agent")}
                    title="에이전트가 질의를 바꿔 가며 여러 번 검색: 느리지만 어려운 질문에 유리">에이전트</button>
          </div>
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
          <button className="button send" disabled={pending || !text.trim()} aria-label="보내기">보내기</button>
        </form>
      </main>
      )}

      {view === "chat" && source && (
        <aside className="source">
          <header>
            <div>
              <div className="source-title">{source.title}</div>
              <div className="source-where">{version(source.heading).base}{source.page_start ? ` · p.${source.page_start}` : ""}</div>
              <Badge heading={source.heading} />
            </div>
            <button className="link" onClick={() => setSource(null)} aria-label="닫기">닫기</button>
          </header>
          <small className="meta">{source.doc_id} · 글자 {source.start}–{source.end}{source.ocr ? " · OCR로 읽은 쪽" : ""}</small>
          <pre>{source.text}</pre>
        </aside>
      )}
    </div>
  );
}
