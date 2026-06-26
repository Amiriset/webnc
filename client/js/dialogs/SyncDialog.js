// ── frontend/dialogs/SyncDialog.js ─── Synchronize Directories (TC-style) ───
const { useState, useEffect } = React;
const h = React.createElement;
import { fmtSize, fmtDate, toWinPath } from "../lib/utils.js";

export function SyncDialog({ plan, actions, leftPath, rightPath, onCompare, onToggle, onSetAll, onExecute, onClose, status }) {
  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); }
      if (e.key === "Enter" && status === "plan" && actions.length > 0) onExecute();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose, onExecute, status, actions.length]);

  const isSetup = status === "setup";
  const hasPlan = plan && plan.length > 0;

  // ── Setup state ──
  const [filter, setFilter] = useState("*.*");
  const [subdirs, setSubdirs] = useState(true);
  const [byContent, setByContent] = useState(false);
  const [ignoreDate, setIgnoreDate] = useState(false);
  const [asymmetric, setAsymmetric] = useState(false);

  // ── Show-filter toggles (TC style: → = ← ≠) ──
  const [sfRight, setSfRight] = useState(true);
  const [sfEqual, setSfEqual] = useState(true);
  const [sfNotEq, setSfNotEq] = useState(true);
  const [sfLeft, setSfLeft] = useState(true);

  // ── Counts ──
  const cSame = plan.filter((i) => i.status === "same").length;
  const cDiff = plan.filter((i) => i.status === "different").length;
  const cOnlyL = plan.filter((i) => i.status === "only_left").length;
  const cOnlyR = plan.filter((i) => i.status === "only_right").length;
  const cActs = (a) => actions.filter((x) => x.action === a).length;
  const cActsL = cActs("copy_left_to_right") + cActs("delete_left");
  const cActsR = cActs("copy_right_to_left") + cActs("delete_right");

  // ── Icon for the Dir column ──
  const dirIcon = (item) => {
    const a = actions.find((x) => x.name === item.path);
    if (a) {
      if (a.action === "copy_left_to_right" || a.action === "delete_left") return "→";
      if (a.action === "copy_right_to_left" || a.action === "delete_right") return "←";
    }
    if (item.status === "same") return "=";
    if (item.status === "different") return "≠";
    if (item.status === "only_left") return "→";
    if (item.status === "only_right") return "←";
    return "?";
  };

  const dirColor = (item) => {
    const a = actions.find((x) => x.name === item.path);
    if (a) return a.action.startsWith("copy_left") || a.action === "delete_left" ? "#FFFF00" : "#FF8800";
    if (item.status === "same") return "#666";
    if (item.status === "different") return "#FF4444";
    if (item.status === "only_left") return "#55FF55";
    if (item.status === "only_right") return "#FF8800";
    return "#888";
  };

  // ── Available actions per status ──
  const actionCycle = {
    only_left:  ["copy_left_to_right", null],
    only_right: [asymmetric ? "delete_right" : "copy_right_to_left", null],
    different:  ["copy_left_to_right", "copy_right_to_left", null],
    same:       [],
  };

  const handleRowClick = (item) => {
    const opts = actionCycle[item.status] || [];
    if (!opts.length) return;
    const cur = actions.find((a) => a.name === item.path);
    const curAct = cur ? cur.action : null;
    const idx = curAct ? opts.indexOf(curAct) : -1;
    const next = idx >= 0 && idx < opts.length - 1 ? opts[idx + 1] : opts[0];
    onToggle(item.path, next);
  };

  // ── Does item pass current show filters? ──
  const passes = (item) => {
    const a = actions.find((x) => x.name === item.path);
    const hasAct = !!a;
    if (sfRight && hasAct && (a.action === "copy_left_to_right" || a.action === "delete_left")) return true;
    if (sfLeft  && hasAct && (a.action === "copy_right_to_left" || a.action === "delete_right")) return true;
    if (sfNotEq && item.status === "different" && !hasAct) return true;
    if (sfEqual && item.status === "same") return true;
    if (sfRight && item.status === "only_left" && !hasAct) return true;
    if (sfLeft  && item.status === "only_right" && !hasAct) return true;
    return false;
  };
  const filtered = plan.filter(passes);

  const sfStyle = (on) => ({
    cursor: "pointer", padding: "1px 6px", fontSize: 11,
    color: on ? "#000" : "#888", background: on ? "#00AAAA" : "transparent",
    border: "1px solid " + (on ? "#00AAAA" : "#444"), lineHeight: "16px",
  });

  // ── Results view ──
  if (status === "result") return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(600px, 90vw)", maxHeight: "70vh" } },
      h("div", { className: "title-bar" }, "── Sync Results ──"),
      h("div", { style: { flex: 1, overflowY: "auto", padding: "2px 0" } },
        plan.map((r) => h("div", { key: r.name, style: { display: "flex", padding: "1px 6px", gap: 6, fontSize: 11, color: r.ok ? "#00FF00" : "#FF4444" } },
          h("span", { style: { width: 90, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, r.action),
          h("span", { style: { flex: 1 } }, r.name),
          h("span", {}, r.ok ? "OK" : r.error || "ERROR")))),
      h("div", { className: "footer-bar", style: { fontSize: 10 } }, "Esc to close")));

  // ── Main render ──
  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(900px, 96vw)", maxHeight: "88vh" } },

      h("div", { className: "title-bar" }, "── Synchronize Directories ──"),

      // Setup panel
      h("div", { className: "bor-bot-blue", style: { padding: "4px 8px", flexShrink: 0, fontSize: 11 } },
        h("div", { className: "flex", style: { marginBottom: 2 } },
          h("span", { className: "text-yellow flex-shrink0", style: { width: 48 } }, "Left:"),
          h("span", { className: "text-cyan" }, toWinPath(leftPath))),
        h("div", { className: "flex", style: { marginBottom: 3 } },
          h("span", { className: "text-yellow flex-shrink0", style: { width: 48 } }, "Right:"),
          h("span", { className: "text-cyan" }, toWinPath(rightPath))),
        h("div", { className: "flex gap-4", style: { alignItems: "center", marginBottom: 3, flexWrap: "wrap" } },
          h("span", { className: "text-yellow" }, "Filter:"),
          h("input", { value: filter, onChange: (e) => setFilter(e.target.value), className: "nc-input", style: { width: 90, fontSize: 11, padding: "1px 4px" } }),
          h("span", { onClick: () => setSubdirs((v) => !v), className: "nc-toggle", style: { color: subdirs ? "#55FF55" : "#FF5555", padding: "1px 4px" } }, subdirs ? "[x] Subdirs" : "[ ] Subdirs"),
          h("span", { onClick: () => setByContent((v) => !v), className: "nc-toggle", style: { color: byContent ? "#55FF55" : "#FF5555", padding: "1px 4px" } }, byContent ? "[x] By content" : "[ ] By content"),
          h("span", { onClick: () => setIgnoreDate((v) => !v), className: "nc-toggle", style: { color: ignoreDate ? "#55FF55" : "#FF5555", padding: "1px 4px" } }, ignoreDate ? "[x] Ignore date" : "[ ] Ignore date"),
          h("span", { onClick: () => setAsymmetric((v) => !v), className: "nc-toggle", style: { color: asymmetric ? "#FF8800" : "#FF5555", padding: "1px 4px" } }, asymmetric ? "[x] Asymmetric" : "[ ] Asymmetric")),
        isSetup
          ? h("div", { className: "text-center", style: { padding: "4px" } },
              h("button", { onClick: () => onCompare({ filter, subdirs, byContent, ignoreDate, asymmetric }),
                className: "nc-btn-primary" }, "[ Compare ]"))
          : null),

      // Results area
      isSetup ? null :
        h("div", { className: "flex-col flex-1", style: { minHeight: 0 } },

          // Show-filter bar
          hasPlan ? h("div", { className: "flex gap-2", style: { padding: "2px 6px", borderBottom: "1px solid #003366", flexShrink: 0, alignItems: "center" } },
            h("span", { style: { color: "#888", fontSize: 10, marginRight: 2 } }, "Show:"),
            h("span", { style: sfStyle(sfRight), onClick: () => setSfRight((v) => !v) }, "→"),
            h("span", { style: sfStyle(sfEqual), onClick: () => setSfEqual((v) => !v) }, "="),
            h("span", { style: sfStyle(sfNotEq), onClick: () => setSfNotEq((v) => !v) }, "≠"),
            h("span", { style: sfStyle(sfLeft), onClick: () => setSfLeft((v) => !v) }, "←"),
            h("span", { style: { marginLeft: "auto", fontSize: 10, color: "#888" } }, `${cActsL}→ ${cActsR}←`)) : null,

          // Column headers
          hasPlan ? h("div", { className: "flex", style: { padding: "2px 6px", borderBottom: "1px solid #003366", flexShrink: 0, fontSize: 10, color: "#888" } },
            h("span", { className: "flex-1 truncate" }, "Left Name"),
            h("span", { className: "filesize", style: { width: 65 } }, "Size"),
            h("span", { className: "datetime", style: { width: 125 } }, "Modified"),
            h("span", { className: "status-icon", style: { width: 24 } }, ""),
            h("span", { className: "flex-1 truncate" }, "Right Name"),
            h("span", { className: "filesize", style: { width: 65 } }, "Size"),
            h("span", { className: "datetime", style: { width: 125 } }, "Modified")) : null,

          // File rows
          h("div", { className: "scroll-y", style: { padding: "2px 0" } },
            !hasPlan
              ? h("div", { className: "text-center text-yellow", style: { padding: "20px", fontSize: 12 } }, "Directories are identical")
              : !filtered.length
                ? h("div", { className: "text-center", style: { padding: "20px", fontSize: 12, color: "#555599" } }, (sfEqual || sfNotEq || sfRight || sfLeft) ? "No files match current show filters" : "All show filters are off")
                : filtered.map((item) => {
                    const isClickable = item.status === "only_left" || item.status === "only_right" || item.status === "different";
                    const lf = item.left || null;
                    const rf = item.right || null;
                    const nameCell = (src) =>
                      h("span", { className: src?.is_dir ? "directory" : "filename" },
                        src ? (src.is_dir ? `[${src.name ?? item.name}]` : (src.name ?? item.name)) : "");
                    const sizeCell = (src) =>
                      h("span", { className: "filesize", style: { width: 65 } },
                        src ? fmtSize(src.size) : "");
                    const dateCell = (src) =>
                      h("span", { className: "datetime", style: { width: 125 } },
                        src?.modified_ts ? fmtDate(new Date(src.modified_ts * 1000).toISOString()) : "");
                    const hasAction = !!actions.find((a) => a.name === item.path);
                    const rowCls = ["file-row", ...(hasAction ? ["selected"] : []), ...(!isClickable ? ["row-disabled"] : [])].join(" ");
                    return h("div", {
                      key: item.path, className: rowCls,
                      onClick: isClickable ? () => handleRowClick(item) : undefined,
                    },
                      nameCell(lf),
                      sizeCell(lf),
                      dateCell(lf),
                      h("span", { className: "status-icon", style: { width: 24, color: dirColor(item) } }, dirIcon(item)),
                      nameCell(rf),
                      sizeCell(rf),
                      dateCell(rf));
                  })),

          // Info bar
          h("div", { className: "flex gap-8 bor-bot-dk", style: { padding: "2px 6px", flexShrink: 0, fontSize: 10, color: "#888" } },
            h("span", null, `Total: ${plan.length}`),
            h("span", { style: { color: "#006644" } }, `Same: ${cSame}`),
            h("span", { style: { color: "#FF4444" } }, `Diff: ${cDiff}`),
            h("span", { style: { color: "#55FF55" } }, `L-only: ${cOnlyL}`),
            h("span", { style: { color: "#FF8800" } }, `R-only: ${cOnlyR}`)),

          // Buttons
          h("div", { className: "flex gap-4 bor-bot-blue", style: { padding: "4px 6px", justifyContent: "center", flexShrink: 0 } },
            h("button", { onClick: () => onCompare({ filter, subdirs, byContent, ignoreDate, asymmetric }),
              className: "nc-btn", style: { color: "#00FFFF", borderColor: "#00FFFF", fontSize: 10, padding: "2px 8px" } }, "Re-compare"),
            hasPlan ? h("button", { onClick: () => onSetAll(true),
              className: "nc-btn", style: { color: "#FFFF00", borderColor: "#FFFF00", fontSize: 10, padding: "2px 8px" } }, "Mark All") : null,
            h("button", { onClick: actions.length > 0 ? onExecute : undefined, disabled: actions.length === 0,
              className: "nc-btn-primary", style: { fontSize: 11, padding: "2px 16px" } }, "Synchronize"),
            h("button", { onClick: onClose,
              className: "nc-btn", style: { borderColor: "#0055AA", fontSize: 11, padding: "2px 16px" } }, "Close")),

          // Footer
          h("div", { className: "text-center bor-bot-dk", style: { padding: "2px", color: "#888", fontSize: 9, flexShrink: 0 } },
            !hasPlan ? "Directories are identical · Re-compare or Close"
              : actions.length > 0 ? `${actions.length} marked · Click=cycle dir · Enter=execute · Esc=close`
                : "Click file to set direction · Esc=close"))));
}
