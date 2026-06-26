// ── frontend/dialogs/EditorDialog.js ─── In-browser file editor (F4) ─────────
const { useState, useEffect, useRef } = React;
const h = React.createElement;

export function EditorDialog({ filename, content, onSave, onClose }) {
  const [text, setText] = useState(content);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const textRef = useRef(null);

  useEffect(() => { textRef.current?.focus(); }, []);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") { e.preventDefault(); if (dirty) { if (confirm("Discard changes?")) onClose(); } else onClose(); }
      if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "S")) { e.preventDefault(); doSave(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [dirty, onClose]);

  const onChange = (e) => { setText(e.target.value); setDirty(true); };

  const doSave = async () => {
    setSaving(true);
    try { await onSave(text); setDirty(false); } catch (err) { alert("Save failed: " + err.message); }
    finally { setSaving(false); }
  };

  return h("div", { className: "overlay", style: { background: "rgba(0,0,0,0.7)" }, onClick: () => { if (dirty) { if (confirm("Discard changes?")) onClose(); } } },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(780px, 94vw)", maxHeight: "88vh", fontSize: 13 } },
      h("div", { className: "title-bar flex", style: { justifyContent: "space-between" } },
        h("span", null, `── Edit: ${filename} ──`),
        h("span", { style: { color: "#FFFF00", fontSize: 10 } }, dirty ? "[Modified]" : "")),
      h("textarea", {
        ref: textRef, value: text, onChange: onChange,
        style: { flex: 1, margin: 0, padding: "8px 12px", color: "#00FFFF", background: "#000040", border: "none", outline: "none", fontFamily: '"Lucida Console", "Courier New", monospace', fontSize: 13, lineHeight: 1.4, resize: "none", minHeight: 200 },
      }),
      h("div", { className: "flex", style: { justifyContent: "center", gap: 16, padding: "6px 12px 10px", borderTop: "1px solid #0055AA", flexShrink: 0 } },
        h("button", { onClick: doSave, disabled: saving, className: "nc-btn-primary" }, saving ? "Saving..." : "[ Save ]"),
        h("button", { onClick: () => { if (dirty) { if (confirm("Discard changes?")) onClose(); } else onClose(); }, className: "nc-btn", style: { borderColor: "#0055AA" } }, "[ Cancel ]")),
      h("div", { className: "footer-bar", style: { fontSize: 10 } }, "Ctrl+S to save · Esc to close")));
}
