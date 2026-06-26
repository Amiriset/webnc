// ── frontend/dialogs/HistoryDialog.js ─── Directory History ─────────────────
const { useState, useEffect, useRef } = React;
const h = React.createElement;
import { toWinPath } from "../lib/utils.js";

export function HistoryDialog({ entries, activePanel, onClose, onNavigate }) {
  const [selIdx, setSelIdx] = useState(entries.length - 1);
  const listRef = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
      if (e.key === "ArrowDown") { e.preventDefault(); setSelIdx((s) => Math.min(entries.length - 1, s + 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setSelIdx((s) => Math.max(0, s - 1)); }
      if (e.key === "Enter") { e.preventDefault(); if (entries[selIdx]) { onNavigate(entries[selIdx], activePanel); onClose(); } }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [entries, selIdx, onClose, onNavigate, activePanel]);

  useEffect(() => {
    if (listRef.current) {
      const row = listRef.current.querySelector(`[data-idx="${selIdx}"]`);
      if (row) row.scrollIntoView({ block: "nearest" });
    }
  }, [selIdx]);

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(500px, 85vw)", maxHeight: "70vh" } },
      h("div", { className: "title-bar" }, "── Directory History ──"),
      h("div", { ref: listRef, className: "scroll-y", style: { padding: "4px 0" } },
        entries.length === 0 ? h("div", { className: "text-center", style: { padding: 20, color: "#555599" } }, "(empty)") :
        entries.map((p, i) =>
          h("div", {
            key: i, "data-idx": i,
            style: { padding: "2px 8px", cursor: "pointer", color: i === selIdx ? "#000" : "#00FFFF", background: i === selIdx ? "#00AAAA" : "transparent" },
            onClick: () => setSelIdx(i),
            onDoubleClick: () => { onNavigate(p, activePanel); onClose(); },
          },
            h("span", { style: { color: "#888", marginRight: 8 } }, `${i + 1}.`),
            h("span", null, toWinPath(p))))),
      h("div", { className: "footer-bar", style: { fontSize: 10 } },
        `↑↓ select · Enter navigate · Esc close · ${entries.length} entries`)));
}
