// ── frontend/dialogs/DriveDialog.js ─── Drive selector (Alt+F1/F2) ──────────
const { useState, useEffect } = React;
const h = React.createElement;
import { fmtSize } from "../lib/utils.js";

export function DriveDialog({ drives, onSelect, onClose }) {
  const [sel, setSel] = useState(0);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
      if (e.key === "ArrowUp") { e.preventDefault(); setSel((s) => Math.max(0, s - 1)); }
      if (e.key === "ArrowDown") { e.preventDefault(); setSel((s) => Math.min(drives.length - 1, s + 1)); }
      if (e.key === "Enter") { e.preventDefault(); if (drives[sel]) onSelect(drives[sel]); }
      if (e.key.length === 1 && e.key.match(/[a-z]/i)) {
        e.preventDefault();
        const i = drives.findIndex((d) => d.drive[0].toUpperCase() === e.key.toUpperCase());
        if (i >= 0) setSel(i);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [drives, sel, onSelect, onClose]);

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { fontSize: 13, minWidth: 300 } },
      h("div", { className: "title-bar" }, "── Select Drive ──"),
      h("div", { style: { padding: "4px 8px" } },
        h("div", { className: "flex text-yellow fs-12 bor-bot-blue", style: { padding: "2px 4px" } },
          h("span", { style: { width: 40 } }, "Drv"),
          h("span", { style: { flex: "0 0 140px" } }, "Label"),
          h("span", { className: "flex-1 text-right" }, "Free space")),
        drives.map((d, i) =>
          h("div", {
            key: d.drive,
            onClick: () => onSelect(d),
            className: "flex",
            style: { padding: "2px 4px", fontSize: 12, lineHeight: "18px", cursor: "pointer", background: i === sel ? "#00AAAA" : "transparent", color: i === sel ? "#000" : "#00FFFF" },
          },
            h("span", { style: { width: 40, fontWeight: "bold" } }, d.drive[0]),
            h("span", { style: { flex: "0 0 140px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, d.label),
            h("span", { className: "flex-1 text-right" }, fmtSize(d.free) + " free of " + fmtSize(d.total))))),
      h("div", { className: "text-center text-yellow fs-11", style: { padding: "4px 8px 8px" } }, "Arrow keys / Letter · Enter select · Esc cancel")));
}
