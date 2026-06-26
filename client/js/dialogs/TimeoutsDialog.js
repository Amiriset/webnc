// ── frontend/dialogs/TimeoutsDialog.js ─── Operation timeouts config ─────────
const { useState, useEffect } = React;
const h = React.createElement;
import { apiGetConfig, apiSetConfig } from "../lib/api.js";

const OP_KEYS = [
  { key: "copy", label: "Copy" },
  { key: "move", label: "Move" },
  { key: "batch_delete", label: "Batch Delete" },
  { key: "search", label: "Search" },
  { key: "compare", label: "Compare Dirs" },
  { key: "sync_plan", label: "Sync Plan" },
  { key: "sync_execute", label: "Sync Execute" },
  { key: "archive_list", label: "Archive List" },
];

export function TimeoutsDialog({ onClose }) {
  const [opCfg, setOpCfg] = useState(null);
  const [loadErr, setLoadErr] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") { e.preventDefault(); onClose(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  useEffect(() => {
    (async () => {
      try { setOpCfg(await apiGetConfig()); } catch (e) { setLoadErr(e.message); }
    })();
  }, []);

  const updateOp = (key, field, val) => {
    setOpCfg((prev) => {
      const ops = { ...prev.operations };
      ops[key] = { ...ops[key], [field]: val };
      return { ...prev, operations: ops };
    });
  };

  const opNum = (key, field, val, min, max) =>
    h("input", {
      type: "number", value: val, onChange: (e) => updateOp(key, field, Math.max(min, Number(e.target.value))),
      min, max, className: "nc-num",
    });

  const handleSave = async () => {
    try { await apiSetConfig(opCfg); setSaved(true); setTimeout(() => setSaved(false), 2000); }
    catch (e) { setLoadErr(e.message); }
  };

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(520px, 90vw)", maxHeight: "85vh", fontSize: 13 } },
      h("div", { className: "title-bar" }, "── Operation Timeouts ──"),
      loadErr ? h("div", { className: "text-center text-red fs-11", style: { padding: "4px 8px" } }, loadErr) : null,
      saved ? h("div", { className: "text-center", style: { padding: "2px 8px", color: "#55FF55", fontSize: 11 } }, "Saved") : null,
      // Table header
      h("div", { className: "flex bor-bot-dk flex-shrink0", style: { padding: "3px 6px", fontSize: 10, color: "#888" } },
        h("span", { style: { width: 110 } }, "Operation"),
        h("span", { className: "text-center", style: { width: 70 } }, "Retries"),
        h("span", { className: "text-center", style: { width: 80 } }, "Timeout (s)"),
        h("span", { className: "text-center", style: { width: 80 } }, "Interval (ms)")),
      // Table body
      h("div", { className: "scroll-y", style: { padding: "2px 0" } },
        !opCfg && !loadErr
          ? h("div", { className: "text-center", style: { padding: 20, color: "#555599", fontSize: 11 } }, "Loading...")
          : opCfg && OP_KEYS.map(({ key, label }) => {
              const o = opCfg.operations?.[key] || {};
              return h("div", { key, className: "flex fs-11 bor-bot-dk", style: { padding: "2px 6px", alignItems: "center", borderBottom: "1px solid #002244" } },
                h("span", { style: { width: 110, color: "#00FFFF" } }, label),
                h("span", { className: "text-center", style: { width: 70 } }, opNum(key, "max_retries", o.max_retries ?? 3, 0, 10)),
                h("span", { className: "text-center", style: { width: 80 } }, opNum(key, "timeout", o.timeout ?? 120, 5, 3600)),
                h("span", { className: "text-center", style: { width: 80 } }, opNum(key, "interval", o.interval ?? 300, 50, 10000)));
            })),
      // Buttons
      h("div", { className: "flex gap-16", style: { justifyContent: "center", padding: "6px 12px 10px", flexShrink: 0 } },
        h("button", { onClick: handleSave, className: "nc-btn" }, "[ Save ]"),
        h("button", { onClick: onClose, className: "nc-btn" }, "[ Cancel ]")),
      h("div", { className: "text-center", style: { padding: "2px 8px 6px", color: "#555599", fontSize: 9, flexShrink: 0 } },
        "Esc to close · Settings apply on next operation")));
}
