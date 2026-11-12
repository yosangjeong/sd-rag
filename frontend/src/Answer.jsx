// The answer text: the small Markdown subset the model writes (paragraphs, **bold**,
// "1." and "-"/"*" lists, "#" headings) plus "[n]" citation buttons. Built as React
// elements, never as HTML strings, so text from documents cannot inject markup.

function inline(text, byN, onOpen, keyBase) {
  // split on citations and **bold**, keep the delimiters
  return text.split(/(\[\d+\]|\*\*[^*]+\*\*)/).map((part, i) => {
    const key = `${keyBase}-${i}`;
    const cite = part.match(/^\[(\d+)\]$/);
    if (cite) {
      const c = byN[cite[1]];
      return c ? (
        <button key={key} className="cite" title={c.label} onClick={() => onOpen(c)}>{cite[1]}</button>
      ) : null; // the API already drops numbers that are not sources
    }
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={key}>{part.slice(2, -2)}</strong>;
    return <span key={key}>{part}</span>;
  });
}

export default function Answer({ text, citations, onOpen, label }) {
  const byN = Object.fromEntries(citations.map((c) => [c.n, { ...c, label: label(c) }]));
  const blocks = [];
  let list = null; // {ordered, items}
  const flush = () => {
    if (list) blocks.push(list);
    list = null;
  };
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    const ol = line.match(/^(\d+)[.)]\s+(.*)$/);
    const ul = line.match(/^[-*•]\s+(.*)$/);
    if (ol || ul) {
      const ordered = Boolean(ol);
      if (!list || list.ordered !== ordered) {
        flush();
        list = { type: "list", ordered, items: [] };
      }
      list.items.push(ol ? ol[2] : ul[1]);
      continue;
    }
    flush();
    if (!line) continue;
    const h = line.match(/^#{1,4}\s+(.*)$/);
    blocks.push(h ? { type: "heading", text: h[1] } : { type: "p", text: line });
  }
  flush();
  return (
    <div className="answer">
      {blocks.map((b, i) => {
        if (b.type === "list") {
          const Tag = b.ordered ? "ol" : "ul";
          return <Tag key={i}>{b.items.map((t, j) => <li key={j}>{inline(t, byN, onOpen, `${i}-${j}`)}</li>)}</Tag>;
        }
        if (b.type === "heading") return <h4 key={i}>{inline(b.text, byN, onOpen, i)}</h4>;
        return <p key={i}>{inline(b.text, byN, onOpen, i)}</p>;
      })}
    </div>
  );
}

// Sources list: citations of the same place (several chunks of one article) on one line
export function Sources({ citations, onOpen, label }) {
  const groups = [];
  for (const c of citations) {
    const l = label(c);
    const g = groups.find((x) => x.label === l);
    if (g) g.items.push(c);
    else groups.push({ label: l, items: [c] });
  }
  return (
    <ul className="sources">
      {groups.map((g) => (
        <li key={g.label}>
          <span className="nums">{g.items.map((c) => c.n).join(", ")}.</span>{" "}
          <button className="link" onClick={() => onOpen(g.items[0])}>{g.label}</button>
        </li>
      ))}
    </ul>
  );
}
