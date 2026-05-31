// ── frontend/dialogs/CompareDialog.js ─── Compare Directories ───────────────
const { useState, useEffect } = React;
const h = React.createElement;
import { fmtSize } from "../lib/utils.js";

export function CompareDialog({ data, leftPath, rightPath, onClose, onNavigate }) {
  useEffect(() => {
    const handler = (e) => { if (["Escape", "Enter"].includes(e.key)) { e.preventDefault(); onClose(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!data) return null;
  const [tab, setTab] = useState("diff");
  const tabStyle = (active) => ({
    cursor: "pointer", padding: "2px 10px",
    color: active ? "#000" : "#00FFFF",
    background: active ? "#00AAAA" : "#000080",
    borderBottom: active ? "2px solid #00FFFF" : "2px solid transparent",
  });

  const renderRow = (item, sideLabel) =>
    h("div", {
      key: item.name, className: "flex fs-11",
      style: { padding: "1px 6px", gap: 6, cursor: "pointer", color: "#00FFFF" },
      onClick: () => { if (sideLabel === "L") onNavigate(item, "left"); else onNavigate(item, "right"); },
    },
      h("span", { className: "flex-shrink0", style: { width: 24, color: "#888" } }, sideLabel),
      h("span", { className: item.is_dir ? "directory" : "filename" }, item.is_dir ? `[${item.name}]` : item.name),
      h("span", { className: "filesize flex-shrink0", style: { width: 75 } }, item.is_dir ? "<DIR>" : fmtSize(item.size)),
      h("span", { className: "datetime flex-shrink0", style: { width: 140 } }, item.modified || ""));

  const renderDiffRow = (item) =>
    h("div", {
      key: item.name, className: "flex fs-11",
      style: { padding: "1px 6px", gap: 6, cursor: "pointer", color: "#FF8800" },
      onClick: () => onNavigate(item, "left"),
    },
      h("span", { style: { width: 24, color: "#FF8800", flexShrink: 0 } }, "≠"),
      h("span", { style: { flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#FF8800" } }, item.name),
      h("span", { className: "filesize flex-shrink0", style: { width: 75 } }, item.left.is_dir ? "<DIR>" : fmtSize(item.left.size)),
      h("span", { style: { width: 75, textAlign: "right", color: "#FF8800", flexShrink: 0 } }, item.right.is_dir ? "<DIR>" : fmtSize(item.right.size)));

  const items = tab === "left" ? data.only_left : tab === "right" ? data.only_right : tab === "same" ? data.same : data.different;

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(680px, 92vw)", maxHeight: "80vh" } },
      h("div", { className: "title-bar" }, "── Compare Directories ──"),
      h("div", { className: "flex bor-bot-blue flex-shrink0" },
        h("span", { style: tabStyle(tab === "diff"), onClick: () => setTab("diff") }, `Different (${data.different.length})`),
        h("span", { style: tabStyle(tab === "left"), onClick: () => setTab("left") }, `Only Left (${data.only_left.length})`),
        h("span", { style: tabStyle(tab === "right"), onClick: () => setTab("right") }, `Only Right (${data.only_right.length})`),
        h("span", { style: tabStyle(tab === "same"), onClick: () => setTab("same") }, `Same (${data.same.length})`)),
      h("div", { className: "flex bor-bot-dk flex-shrink0", style: { padding: "2px 6px", fontSize: 10, color: "#888" } },
        h("span", { style: { width: 24, flexShrink: 0 } }, ""),
        h("span", { className: "flex-1" }, "Name"),
        h("span", { className: "filesize flex-shrink0", style: { width: 75 } }, "Left"),
        h("span", { className: "filesize flex-shrink0", style: { width: 75 } }, "Right")),
      h("div", { className: "scroll-y", style: { padding: "2px 0" } },
        tab === "diff" ? data.different.map(renderDiffRow) :
        tab === "left" ? data.only_left.map((i) => renderRow(i, "L")) :
        tab === "right" ? data.only_right.map((i) => renderRow(i, "R")) :
        data.same.map((i) => renderRow(i, "="))),
      h("div", { className: "footer-bar", style: { fontSize: 10 } },
        `Total: ${data.left_total} left / ${data.right_total} right · Tab to switch · Click to open · Esc to close`)));
}
