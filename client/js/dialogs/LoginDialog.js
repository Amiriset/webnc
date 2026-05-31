// ── frontend/dialogs/LoginDialog.js ─── Session token entry ─────────────────
const { useState, useEffect, useRef } = React;
const h = React.createElement;

export function LoginDialog({ error, onLogin, onClose }) {
  const [value, setValue] = useState("");
  const inputRef = useRef(null);
  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") e.preventDefault(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  const submit = () => { if (value.trim()) onLogin(value.trim()); };

  return h("div", { className: "overlay", style: { zIndex: 1000, background: "rgba(0,0,0,0.7)" } },
    h("div", { className: "dialog", style: { fontSize: 13, minWidth: 400 } },
      h("div", { className: "title-bar" }, "── WebNC Session Access ──"),
      h("div", { style: { padding: "16px 20px" } },
        h("div", { style: { color: "#00FFFF", marginBottom: 8, fontSize: 11 } }, "Enter the session access token from the server console:"),
        h("input", {
          ref: inputRef, type: "password", value,
          onChange: (e) => setValue(e.target.value),
          onKeyDown: (e) => { if (e.key === "Enter") submit(); },
          className: "nc-input", style: { width: "100%", fontSize: 13, padding: "6px 8px", boxSizing: "border-box" },
        }),
        error ? h("div", { className: "text-red fs-11", style: { marginTop: 6 } }, error) : null),
      h("div", { className: "flex gap-16", style: { justifyContent: "center", padding: "4px 20px 14px" } },
        h("button", { onClick: submit, className: "nc-btn-primary" }, "[ OK ]"),
        h("button", { onClick: onClose, className: "nc-btn", style: { borderColor: "#0055AA" } }, "[ Cancel ]"))));
}
