// ── frontend/dialogs/InfoDialog.js ─── File/Dir info (F4) ───────────────────
const { useEffect } = React;
const h = React.createElement;
import { fmtSize } from "../lib/utils.js";

export function InfoDialog({ info, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (["Escape", "Enter"].includes(e.key)) { e.preventDefault(); onClose(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!info) return null;
  const rows = [
    ["Name", info.name], ["Path", info.path],
    ["Type", info.is_dir ? "Directory" : `File (.${info.extension})`],
    ["Size", info.is_dir ? `${fmtSize(info.total_size || 0)} (${info.file_count} files, ${info.dir_count} dirs)` : fmtSize(info.size)],
    ["Modified", info.modified], ["Created", info.created], ["Accessed", info.accessed],
    ["Owner", info.owner || `${info.owner_uid}:${info.owner_gid}`],
    ["Permissions", info.permissions],
  ];
  if (info.md5) rows.push(["MD5", info.md5]);

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { fontSize: 12, minWidth: 400 } },
      h("div", { className: "title-bar" }, info.is_dir ? "── Directory Info ──" : "── File Info ──"),
      h("div", { style: { padding: "8px 12px" } }, rows.map(([k, v]) =>
        h("div", { key: k, className: "flex", style: { marginBottom: 2 } },
          h("span", { className: "text-yellow flex-shrink0", style: { width: 110 } }, `${k}:`),
          h("span", { style: { color: "#00FFFF", wordBreak: "break-all" } }, v)))),
      h("div", { className: "text-center", style: { padding: "4px 8px 8px" } },
        h("button", { onClick: onClose, className: "nc-btn" }, "[ OK ]"))));
}
