// ── frontend/dialogs/HelpDialog.js ─── Help screen (F1) ────────────────────
const { useEffect } = React;
const h = React.createElement;

export function HelpDialog({ onClose }) {
  useEffect(() => {
    const handler = (e) => { if (["Escape", "Enter", "F1"].includes(e.key)) { e.preventDefault(); onClose(); } };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  const section = (title, items) =>
    h("div", { style: { marginBottom: 6 } },
      h("div", { className: "text-yellow fs-11 fw-bold", style: { marginBottom: 2 } }, title),
      items.map(([k, v]) =>
        h("div", { key: k, className: "flex fs-11", style: { marginBottom: 1 } },
          h("span", { style: { color: "#00FFFF", width: 140, flexShrink: 0 } }, k),
          h("span", { style: { color: "#AAA" } }, v))));

  return h("div", { className: "overlay", style: { background: "rgba(0,0,0,0.7)" }, onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { width: "min(540px, 92vw)", maxHeight: "80vh", fontSize: 13 } },
      h("div", { className: "title-bar" }, "── WebNC Help ──"),
      h("div", { className: "scroll-y", style: { padding: "6px 12px" } },
        section("Navigation", [["↑ / ↓", "Move cursor"], ["Home / End", "Jump to first / last"], ["PgUp / PgDn", "Scroll 15 items"], ["Enter", "Open / enter"], ["Tab", "Switch panel"], ["Insert", "Select / deselect"]]),
        section("Function Keys", [["F1", "Help"], ["F3", "View file"], ["F4", "File info"], ["F5", "Copy"], ["F6", "Move / rename"], ["F7", "Create dir"], ["F8", "Delete"], ["F9", "Search"], ["F10", "Logout"]]),
        section("Selection", [["Insert", "Toggle selection"], ["+ (Numpad)", "Select group"], ["− (Numpad)", "Deselect group"], ["* (Numpad)", "Invert selection"]]),
        section("Panels", [["Alt+F1", "Left panel drive"], ["Alt+F2", "Right panel drive"], ["Ctrl+O", "Toggle panels"]]),
        section("View Modes", [["Brief", "Multi-column listing"], ["Full", "Table: name/size/date"], ["Quick view", "Preview opposite selection"], ["Info", "Directory summary"], ["Tree", "Directory tree"]]),
        section("Commands", [["Find File", "Search by pattern"], ["History", "Directory history"], ["System Info", "OS, CPU, RAM"], ["Swap panels", "Exchange L/R paths"], ["Compare Dirs", "Show differences"], ["Sync Dirs", "Synchronize files"], ["Configuration", "Settings"]])),
      h("div", { className: "footer-bar", style: { fontSize: 10 } }, "Esc / Enter / F1 to close")));
}
