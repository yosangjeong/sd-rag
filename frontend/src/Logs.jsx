// Log viewer for evaluator accounts: fixed queries (backend api/logs_api.py PRESETS).
import { useState } from "react";
import { api } from "./api";

const PRESETS = {
  recent: "최근 요청·질문·답변·오류",
  latency_cost: "모드별 지연·토큰",
  tool_calls: "에이전트 도구 호출",
  errors: "오류",
  audit: "감사 기록 (검색·열람)",
  ingest: "업로드 처리",
  request: "요청 ID 하나의 전체 흐름",
};

export default function Logs() {
  const [preset, setPreset] = useState("recent");
  const [minutes, setMinutes] = useState(60);
  const [rid, setRid] = useState("");
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const run = async () => {
    setError("");
    try {
      setRows(await api.logs(preset, minutes, rid));
    } catch (e) {
      setError(e.message);
    }
  };
  const cols = rows && rows.length ? [...new Set(rows.flatMap((r) => Object.keys(r)))] : [];
  return (
    <div className="logs">
      <div className="logbar">
        <select value={preset} onChange={(e) => setPreset(e.target.value)}>
          {Object.entries(PRESETS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={minutes} onChange={(e) => setMinutes(Number(e.target.value))}>
          <option value={60}>최근 1시간</option>
          <option value={1440}>최근 24시간</option>
          <option value={10080}>최근 7일</option>
        </select>
        {preset === "request" && (
          <input value={rid} onChange={(e) => setRid(e.target.value.trim())} placeholder="x-request-id" />
        )}
        <button className="button" onClick={run}>조회</button>
      </div>
      <p className="hint">개인정보·비밀값은 기록 전에 가려지고, 사용자는 해시로만 표시됩니다.</p>
      {error && <p className="error">{error}</p>}
      {rows && (
        <div className="tablewrap">
          <table>
            <thead><tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>{cols.map((c) => <td key={c}>{typeof r[c] === "object" ? JSON.stringify(r[c]) : String(r[c] ?? "")}</td>)}</tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && <p className="hint">결과 없음</p>}
        </div>
      )}
    </div>
  );
}
