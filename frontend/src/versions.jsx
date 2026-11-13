// Statute versions in a chunk heading (backend ingest/parse.py mark_versions):
//   "제18조의3(난임치료휴가) [2026. 11. 27. 시행]"          the amended version
//   "제18조의3(난임치료휴가) [개정 전, 2026. 11. 27. 전까지]"  the version before it
// The label states dates only; whether the version is in force is decided here with
// today's date in Korea, as the answer step does on the server (agent/answer.py).

const AMENDED = /\s*\[(\d{4})\. (\d{1,2})\. (\d{1,2})\. 시행\]$/;
const BEFORE = /\s*\[개정 전, (\d{4})\. (\d{1,2})\. (\d{1,2})\. 전까지\]$/;

function todayKST() {
  const now = new Date(Date.now() + 9 * 3600 * 1000); // Korea: UTC+9, no daylight saving
  return now.toISOString().slice(0, 10);
}

const iso = (m) => `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}`;
const shown = (m) => `${m[1]}. ${m[2]}. ${m[3]}.`;

// { heading without the label, badge: {text, kind} | null }; kind: current | future | old
export function version(heading) {
  const h = heading || "";
  const today = todayKST();
  let m = h.match(AMENDED);
  if (m) {
    const base = h.slice(0, m.index);
    return today >= iso(m)
      ? { base, badge: { text: `현행 · ${shown(m)} 시행`, kind: "current" } }
      : { base, badge: { text: `시행 예정 · ${shown(m)}`, kind: "future" } };
  }
  m = h.match(BEFORE);
  if (m) {
    const base = h.slice(0, m.index);
    return today < iso(m)
      ? { base, badge: { text: `현행 · ${shown(m)} 개정 시행 전`, kind: "current" } }
      : { base, badge: { text: `개정 전 · ${shown(m)}까지`, kind: "old" } };
  }
  return { base: h, badge: null };
}

export function Badge({ heading }) {
  const b = version(heading).badge;
  return b ? <span className={`badge ${b.kind}`}>{b.text}</span> : null;
}
