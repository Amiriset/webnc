// ── frontend/dialogs/ArchiveDialog.js ─── Archive viewer ────────────────────
const { useState, useEffect } = React;
const h = React.createElement;
import { fmtSize, fmtDate } from "../lib/utils.js";

export function ArchiveDialog({ state, onClose, onNavigate }) {
  const [selIdx, setSelIdx] = useState(0);
  const data = state.data;

  useEffect(() => {
    const handler = (e) => {
      if (["Escape", "Enter"].includes(e.key)) { e.preventDefault(); onClose(); }
      if (e.key === "ArrowDown") { e.preventDefault(); setSelIdx((s) => Math.min(data ? data.items.length - 1 : 0, s + 1)); }
      if (e.key === "ArrowUp") { e.preventDefault(); setSelIdx((s) => Math.max(0, s - 1)); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [data, onClose]);

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(680px, 92vw)", maxHeight: "80vh" } },
      h("div", { className: "title-bar" }, `── Archive: ${state.name} ──`),
      h("div", { className: "scroll-y", style: { padding: "2px 0" } },
        state.loading ? h("div", { className: "text-center text-yellow", style: { padding: 20 } }, "Reading archive...") :
        state.error ? h("div", { className: "text-center text-red", style: { padding: 20 } }, state.error) :
        !data || !data.items || data.items.length === 0 ? h("div", { className: "text-center", style: { padding: 20, color: "#555599" } }, "(empty archive)") :
        data.items.map((item, i) =>
          h("div", {
            key: item.name, className: "flex fs-11",
            style: { padding: "1px 6px", gap: 6, cursor: "pointer", color: i === selIdx ? "#000" : "#00FFFF", background: i === selIdx ? "#00AAAA" : "transparent" },
            onClick: () => setSelIdx(i),
          },
            h("span", { className: item.is_dir ? "directory" : "filename" }, item.is_dir ? `[${item.name}]` : item.name),
            h("span", { className: "filesize", style: { width: 75 } }, item.is_dir ? "<DIR>" : fmtSize(item.size)),
            h("span", { className: "datetime", style: { width: 140 } }, fmtDate(item.modified))))),
      h("div", { className: "footer-bar", style: { fontSize: 10 } },
        data ? `${data.items?.length || 0} items · Total: ${fmtSize(data.total_size || 0)} · Esc to close` : "Esc to close")));
}
