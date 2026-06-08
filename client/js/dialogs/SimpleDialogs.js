// ── frontend/dialogs/SimpleDialogs.js ─── FileViewer, Confirm, Input ─────────
const { useState, useEffect, useRef } = React;
const h = React.createElement;

// ── File Viewer (F3) ────────────────────────────────────────────────────────
export function FileViewer({ filename, content, loading, onClose, type, src }) {
  useEffect(() => {
    const handler = (e) => {
      if (["Escape", "Enter", "F10"].includes(e.key)) { e.preventDefault(); onClose(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const title = type === "image" ? `── View: ${filename} ──` : `── View: ${filename} ──`;

  let body;
  if (loading) {
    body = h("div", { className: "text-center text-yellow", style: { padding: 20 } }, "Loading...");
  } else if (type === "image") {
    body = h("div", { className: "flex", style: { justifyContent: "center", alignItems: "center", minHeight: 100, padding: 8 } },
      h("img", { src, style: { maxWidth: "100%", maxHeight: "65vh", objectFit: "contain" }, alt: filename }));
  } else if (type === "html") {
    body = h("iframe", { srcDoc: content, style: { width: "100%", height: "65vh", border: "none", background: "#FFF", color: "#000" }, title: filename, sandbox: "allow-same-origin" });
  } else {
    body = h("pre", {
      className: "scroll-y",
      style: { margin: 0, padding: "8px 12px", color: "#00FFFF", whiteSpace: "pre-wrap", wordBreak: "break-all", lineHeight: 1.4, minHeight: 100 },
    }, content);
  }

  return h("div", { className: "overlay", style: { background: "rgba(0,0,0,0.7)" }, onClick: onClose },
    h("div", {
      onClick: (e) => e.stopPropagation(),
      className: "dialog", style: { width: "min(780px, 94vw)", maxHeight: "82vh", fontSize: 13 },
    },
      h("div", { className: "title-bar flex", style: { justifyContent: "space-between" } },
        h("span", null, title),
        h("span", { style: { cursor: "pointer" }, onClick: onClose }, "✕")),
      body,
      h("div", { className: "text-center text-yellow bor-bot-blue", style: { padding: "2px 8px" } },
        "─── ESC / Enter / F10 to close ──")));
}

// ── Confirm Dialog (Yes/No) ─────────────────────────────────────────────────
export function ConfirmDialog({ title, message, onYes, onNo }) {
  useEffect(() => {
    const handler = (e) => {
      if (["y", "Y", "Enter"].includes(e.key)) { e.preventDefault(); onYes(); }
      if (["n", "N", "Escape"].includes(e.key)) { e.preventDefault(); onNo(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onYes, onNo]);

  return h("div", { className: "overlay" },
    h("div", {
      style: { background: "#AA0000", border: "2px solid #FFFF00", fontFamily: '"Lucida Console", "Courier New", monospace', fontSize: 13, minWidth: 320, boxShadow: "4px 4px 0 rgba(0,0,0,0.5)" },
    },
      h("div", { style: { background: "#FFFF00", color: "#AA0000", padding: "2px 8px", fontWeight: "bold", textAlign: "center" } }, title),
      h("div", { style: { color: "#FFF", padding: "12px 16px", textAlign: "center" } }, message),
      h("div", { className: "flex gap-16", style: { justifyContent: "center", padding: "8px 16px 12px" } },
        h("button", { onClick: onYes, className: "nc-btn" }, "[ Yes ]"),
        h("button", { onClick: onNo, className: "nc-btn" }, "[ No ]"))));
}

// ── Alert Dialog (red error box with OK) ────────────────────────────────────
export function AlertDialog({ message, onClose }) {
  useEffect(() => {
    const handler = (e) => {
      if (["Enter", "Escape"].includes(e.key)) { e.preventDefault(); onClose(); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return h("div", { className: "overlay" },
    h("div", {
      style: { background: "#AA0000", border: "2px solid #FFFF00", fontFamily: '"Lucida Console", "Courier New", monospace', fontSize: 13, minWidth: 320, maxWidth: "80vw", boxShadow: "4px 4px 0 rgba(0,0,0,0.5)" },
    },
      h("div", { style: { background: "#FFFF00", color: "#AA0000", padding: "2px 8px", fontWeight: "bold", textAlign: "center" } }, "Error"),
      h("div", { style: { color: "#FFF", padding: "12px 16px", textAlign: "center", whiteSpace: "pre-wrap", wordBreak: "break-word" } }, message),
      h("div", { className: "text-center", style: { padding: "4px 16px 12px" } },
        h("button", { onClick: onClose, className: "nc-btn" }, "[ OK ]"))));
}

// ── Input Dialog ────────────────────────────────────────────────────────────
export function InputDialog({ title, label, defaultValue, onOk, onCancel }) {
  const [value, setValue] = useState(defaultValue || "");
  const inputRef = useRef(null);

  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") { e.preventDefault(); onCancel(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onCancel]);

  const submit = () => { if (value.trim()) onOk(value.trim()); };

  return h("div", { className: "overlay" },
    h("div", {
      className: "dialog", style: { fontSize: 13, minWidth: 360 },
    },
      h("div", { className: "title-bar" }, title),
      h("div", { style: { padding: "12px 16px" } },
        h("div", { style: { color: "#00FFFF", marginBottom: 6 } }, label),
        h("input", {
          ref: inputRef, value,
          onChange: (e) => setValue(e.target.value),
          onKeyDown: (e) => { if (e.key === "Enter") submit(); },
          className: "nc-input", style: { width: "100%", fontSize: 13, padding: "4px 6px", boxSizing: "border-box" },
        })),
      h("div", { className: "flex gap-16", style: { justifyContent: "center", padding: "4px 16px 12px" } },
        h("button", { onClick: submit, className: "nc-btn" }, "[ OK ]"),
        h("button", { onClick: onCancel, className: "nc-btn" }, "[ Cancel ]"))));
}
