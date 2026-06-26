// ── frontend/dialogs/SysInfoDialog.js ─── System Information ────────────────
const { useEffect } = React;
const h = React.createElement;
import { fmtSize } from "../lib/utils.js";

export function SysInfoDialog({ data, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (["Escape", "Enter"].includes(e.key)) { e.preventDefault(); onClose(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!data) return null;
  const fmtUptime = (s) => {
    const d = Math.floor(s / 86400); s %= 86400;
    const hr = Math.floor(s / 3600); s %= 3600;
    const m = Math.floor(s / 60); s %= 60;
    return `${d}d ${hr}h ${m}m ${s}s`;
  };
  const rows = [
    ["Operating System", data.os], ["Hostname", data.hostname],
    ["Processor", data.processor], ["Architecture", data.architecture],
    ["Uptime", fmtUptime(data.uptime)],
    ["RAM Total", fmtSize(data.ram_total)], ["RAM Used", fmtSize(data.ram_used)], ["RAM Free", fmtSize(data.ram_free)],
  ];

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { fontSize: 12, minWidth: 480, maxWidth: "90vw", maxHeight: "80vh", overflowY: "auto" } },
      h("div", { className: "title-bar" }, "── System Information ──"),
      h("div", { style: { padding: "8px 12px" } },
        rows.map(([k, v]) =>
          h("div", { key: k, className: "flex", style: { marginBottom: 2 } },
            h("span", { className: "text-yellow flex-shrink0", style: { width: 120 } }, `${k}:`),
            h("span", { style: { color: "#00FFFF", wordBreak: "break-all" } }, v || "-"))),
        data.drives && data.drives.length > 0 && h("div", { style: { marginTop: 6 } },
          h("div", { className: "text-yellow", style: { marginBottom: 2, textDecoration: "underline" } }, "Drives:"),
          data.drives.filter((d) => d.total > 0).map((d) =>
            h("div", { key: d.drive, className: "flex fs-11", style: { marginBottom: 1, whiteSpace: "nowrap" } },
              h("span", { style: { color: "#00FFFF", width: 50, flexShrink: 0 } }, d.drive),
              h("span", { className: "text-gray", style: { width: 130, overflow: "hidden", textOverflow: "ellipsis", flexShrink: 0 } }, d.label),
              h("span", { className: "text-yellow text-right flex-shrink0", style: { width: 85 } }, fmtSize(d.total)),
              h("span", { style: { color: "#888", margin: "0 4px", flexShrink: 0 } }, "|"),
              h("span", { style: { color: "#FF8800", width: 65, textAlign: "right", flexShrink: 0 } }, `${d.percent_used}% used`))))),
      h("div", { className: "text-center bor-bot-blue", style: { padding: "4px 8px 8px", marginTop: 6 } },
        h("button", { onClick: onClose, className: "nc-btn" }, "[ OK ]"))));
}
