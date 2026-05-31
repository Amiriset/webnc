// ── frontend/dialogs/SearchDialog.js ─── Find File (F9 / Alt+F7) ────────────
const { useState, useEffect, useRef } = React;
const h = React.createElement;
import { fmtSize, toWinPath } from "../lib/utils.js";
import { apiSearch } from "../lib/api.js";

export function SearchDialog({ onClose, onNavigate, onResults }) {
  const [pattern, setPattern] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [truncated, setTruncated] = useState(false);
  const [error, setError] = useState(null);
  const [selIdx, setSelIdx] = useState(-1);
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
      if (e.key === "ArrowDown") { e.preventDefault(); setSelIdx((s) => Math.min(results.length - 1, s + 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setSelIdx((s) => Math.max(-1, s - 1)); }
      if (e.key === "Enter" && selIdx >= 0 && results[selIdx]) { e.preventDefault(); onNavigate(results[selIdx]); onClose(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [results, selIdx, onClose, onNavigate]);

  const doSearch = async () => {
    if (!pattern.trim()) return;
    setSearching(true); setError(null); setResults([]); setSearched(false);
    try {
      const data = await apiSearch("/C/", pattern.trim());
      setResults(data.results); setTruncated(data.truncated); setSearched(true); setSelIdx(-1);
      if (onResults) { onResults(data.results, pattern.trim(), data.truncated); onClose(); }
    } catch (e) { setError(e.message); setSearched(true); }
    finally { setSearching(false); }
  };

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(680px, 92vw)", maxHeight: "80vh" } },
      h("div", { className: "title-bar" }, "── Find File ──"),
      h("div", { className: "flex bor-bot-blue", style: { padding: "8px", gap: 6, alignItems: "center" } },
        h("span", { className: "text-yellow" }, "Pattern:"),
        h("input", {
          ref: inputRef, value: pattern,
          onChange: (e) => setPattern(e.target.value),
          onKeyDown: (e) => { if (e.key === "Enter") doSearch(); },
          className: "nc-input", style: { flex: 1, fontSize: 12, padding: "4px 6px" },
        }),
        h("button", {
          onClick: doSearch, disabled: searching,
          className: "nc-btn", style: { fontSize: 12, padding: "4px 12px" },
        }, searching ? "..." : "Search")),
      h("div", { className: "scroll-y", style: { minHeight: 120, padding: "4px 0" } },
        searching ? h("div", { className: "text-center text-yellow", style: { padding: 20 } }, "Searching...") :
        error ? h("div", { className: "text-center text-red", style: { padding: 20 } }, error) :
        !searched ? h("div", { className: "text-center", style: { padding: 20, color: "#555599" } }, "Enter pattern and press Enter (e.g. *.txt)") :
        results.length === 0 ? h("div", { className: "text-center text-yellow", style: { padding: 20 } }, "No files found") :
        h("div", null,
          results.map((r, i) =>
            h("div", {
              key: r.path, className: "flex gap-8",
              style: { padding: "2px 8px", cursor: "pointer", color: i === selIdx ? "#000" : "#00FFFF", background: i === selIdx ? "#00AAAA" : "transparent" },
              onClick: () => { onNavigate(r); onClose(); },
              onMouseEnter: () => setSelIdx(i),
            },
              h("span", { className: r.is_dir ? "directory flex-shrink0" : "filename flex-shrink0", style: { width: 200 } }, r.is_dir ? `[${r.name}]` : r.name),
              h("span", { className: "flex-1 truncate", style: { color: "#AAA" } }, toWinPath(r.path)),
              h("span", { className: "text-yellow text-right flex-shrink0", style: { width: 70 } }, r.is_dir ? "<DIR>" : fmtSize(r.size)))),
          truncated && h("div", { className: "text-center", style: { padding: "4px 8px", color: "#FF8800", fontSize: 11 } }, "⚠ Results truncated (max 100)"))),
      h("div", { className: "footer-bar fs-11" },
        "Enter to search · ↑↓ to select · Enter on result to navigate · Esc to close")));
}
