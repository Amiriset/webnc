// ── frontend/dialogs/ConfigDialog.js ─── Configuration ──────────────────────
const { useState, useEffect } = React;
const h = React.createElement;
import { apiGetConfig, apiSetConfig } from "../lib/api.js";

export function ConfigDialog({ config, onSave, onClose }) {
  const [local, setLocal] = useState({ ...config });
  const [srvCfg, setSrvCfg] = useState(null);
  const [loadErr, setLoadErr] = useState(null);
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") { e.preventDefault(); onClose(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);
  useEffect(() => {
    apiGetConfig().then(c => setSrvCfg(c)).catch(e => setLoadErr(e.message));
  }, []);

  const row = (label, control) =>
    h("div", { className: "flex", style: { alignItems: "center", marginBottom: 5, fontSize: 12 } },
      h("span", { className: "text-yellow flex-shrink0", style: { width: 170 } }, label), control);

  const toggle = (val, set) =>
    h("span", { onClick: () => set(!val), className: "nc-toggle", style: { color: val ? "#55FF55" : "#FF5555" } }, val ? "[Yes]" : "[No]");

  const sel = (val, set, opts) =>
    h("select", { value: val, onChange: (e) => set(e.target.value), className: "nc-input", style: { fontSize: 12, padding: "2px 4px" } },
      opts.map((o) => h("option", { key: o, value: o }, o)));

  const num = (val, set) =>
    h("input", {
      type: "number", value: val, onChange: (e) => set(Number(e.target.value)),
      min: 10, max: 24, className: "nc-num",
    });

  const assocRow = (ext, action, upd) =>
    h("div", { key: ext, className: "flex", style: { alignItems: "center", marginBottom: 3, fontSize: 11 } },
      h("span", { className: "text-cyan", style: { width: 60 } }, ext),
      h("select", { value: action || "", onChange: (e) => upd(ext, e.target.value), className: "nc-input", style: { fontSize: 11, padding: "1px 4px" } },
        ["view", "edit", "archive", "preview", ""].map((o) => h("option", { key: o, value: o }, o || "default"))));

  const updateAssoc = (ext, val) => {
    setSrvCfg((prev) => {
      const assocs = { ...prev.associations, [ext]: val };
      if (!val) delete assocs[ext];
      return { ...prev, associations: assocs };
    });
  };

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(420px, 88vw)", fontSize: 13 } },
      h("div", { className: "title-bar" }, "── Configuration ──"),
      loadErr ? h("div", { className: "text-center text-red fs-11", style: { padding: "4px 8px" } }, loadErr) : null,
      h("div", { className: "scroll-y", style: { padding: "8px 12px", maxHeight: "60vh" } },
        row("Default view mode:", sel(local.defaultView, (v) => setLocal({ ...local, defaultView: v }), ["brief", "full"])),
        row("Default sort by:", sel(local.defaultSortBy, (v) => setLocal({ ...local, defaultSortBy: v }), ["name", "extension", "modified", "size", "unsorted"])),
        row("Sort direction:", sel(local.defaultSortDir, (v) => setLocal({ ...local, defaultSortDir: v }), ["asc", "desc"])),
        row("Show hidden files:", toggle(local.showHidden, (v) => setLocal({ ...local, showHidden: v }))),
        row("Confirm before delete:", toggle(local.confirmDelete, (v) => setLocal({ ...local, confirmDelete: v }))),
        row("Confirm before overwrite:", toggle(local.confirmOverwrite, (v) => setLocal({ ...local, confirmOverwrite: v }))),
        row("Font size:", num(local.fontSize, (v) => setLocal({ ...local, fontSize: v }))),
        h("div", { style: { borderTop: "1px solid #0055AA", marginTop: 6, paddingTop: 4, marginBottom: 4 } },
          h("div", { className: "text-cyan", style: { fontSize: 11, marginBottom: 2 } }, "── Extension Associations (Enter dispatches) ──"),
          !srvCfg ? h("div", { style: { fontSize: 10, color: "#555599" } }, "Loading...") :
          Object.entries(srvCfg.associations || {}).sort(([a], [b]) => a.localeCompare(b)).map(([ext, action]) => assocRow(ext, action, updateAssoc)))),
      h("div", { className: "flex gap-16", style: { justifyContent: "center", padding: "4px 12px 10px" } },
        h("button", { onClick: () => { if (srvCfg) apiSetConfig(srvCfg).catch(e => setLoadErr(e.message)); onSave(local); onClose(); }, className: "nc-btn" }, "[ Save ]"),
        h("button", { onClick: onClose, className: "nc-btn" }, "[ Cancel ]"))));
}
