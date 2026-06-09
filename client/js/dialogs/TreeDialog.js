const { useState, useEffect } = React;
const h = React.createElement;
import { apiTree } from "../lib/api.js";

function flattenTree(nodes) {
  const flat = [];
  const walk = (list, depth) => {
    for (const n of list) {
      n._depth = depth;
      flat.push(n);
      if (n.expanded && n.children) walk(n.children, depth + 1);
    }
  };
  walk(nodes, 0);
  return flat;
}

export function TreeDialog({ onSelect, onClose }) {
  const [roots, setRoots] = useState(null);
  const [cur, setCur] = useState(0);
  const [loadingRoot, setLoadingRoot] = useState(true);

  const toggleNode = async (node) => {
    if (node.loading) return;
    if (node.expanded) {
      node.expanded = false;
      setRoots((prev) => [...prev]);
      return;
    }
    node.loading = true;
    setRoots((prev) => [...prev]);
    try {
      const raw = await apiTree(node.path);
      const dirs = (raw.dirs || []).map((d) => ({ ...d, expanded: false, loading: false, children: [] }));
      node.children = dirs;
      node.expanded = true;
    } catch (err) {
      node.children = [];
    } finally {
      node.loading = false;
      setRoots((prev) => [...prev]);
    }
  };

  const handleEnter = (flat, idx) => {
    const n = flat[idx];
    if (!n) return;
    if (n.expanded) {
      onSelect(n.path);
    } else {
      toggleNode(n);
    }
  };

  useEffect(() => {
    const handler = (e) => {
      if (e.key === "Escape") { e.preventDefault(); onClose(); return; }
      const flat = flattenTree(roots || []);
      if (e.key === "ArrowUp") { e.preventDefault(); setCur((s) => Math.max(0, s - 1)); }
      if (e.key === "ArrowDown") { e.preventDefault(); setCur((s) => Math.min(flat.length - 1, s + 1)); }
      if (e.key === "ArrowRight") { e.preventDefault(); const n = flat[cur]; if (n && !n.expanded) toggleNode(n); }
      if (e.key === "ArrowLeft") { e.preventDefault(); const n = flat[cur]; if (n && n.expanded) toggleNode(n); }
      if (e.key === "Enter") { e.preventDefault(); handleEnter(flat, cur); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [roots, cur, onSelect, onClose]);

  useEffect(() => {
    (async () => {
      try {
        const raw = await apiTree("/");
        const dirs = raw.dirs || [];
        const items = dirs.map((d) => ({ ...d, expanded: false, loading: false, children: [] }));
        setRoots(items);
      } catch (err) {
        setRoots([]);
      } finally {
        setLoadingRoot(false);
      }
    })();
  }, []);

  const flat = flattenTree(roots || []);

  if (loadingRoot) {
    return h("div", { className: "overlay", onClick: onClose },
      h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { fontSize: 13, minWidth: 300 } },
        h("div", { className: "title-bar" }, "── NDC Tree ──"),
        h("div", { className: "text-center", style: { padding: 20, color: "#555599", fontSize: 11 } }, "Loading...")));
  }

  return h("div", { className: "overlay", onClick: onClose },
    h("div", { onClick: (e) => e.stopPropagation(), className: "dialog", style: { fontSize: 13, minWidth: 350, minHeight: "50vh", display: "flex", flexDirection: "column" } },
      h("div", { className: "title-bar" }, "── NDC Tree ──"),
      h("div", { className: "scroll-y", style: { flex: 1, padding: "2px 0" } },
        flat.length === 0 ? h("div", { className: "text-center", style: { padding: 20, color: "#555599", fontSize: 11 } }, "(empty)") :
        flat.map((n, i) => {
          const isCur = i === cur;
          return h("div", {
            key: n.path || i, "data-idx": i,
            style: { display: "flex", cursor: "pointer", color: isCur ? "#000" : "#FFF", background: isCur ? "#00AAAA" : "transparent", padding: "1px 0", fontSize: 12, lineHeight: "18px" },
          },
            h("span", { style: { flexShrink: 0, width: n._depth * 14 } }),
            h("span", {
              onClick: (ev) => { ev.stopPropagation(); toggleNode(n); },
              style: { flexShrink: 0, width: 20, cursor: "pointer", color: isCur ? "#000" : "#AAA" },
            }, n.expanded ? "[-]" : n.loading ? " \u27F3" : "[+]"),
            h("span", {
              onClick: () => setCur(i),
              onDoubleClick: () => onSelect(n.path),
              style: { flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
            }, n.name));
        })),
      h("div", { className: "text-center text-yellow fs-11", style: { padding: "4px 8px 8px" } },
        "\u2191\u2193 Navigate  \u2192 Expand / Collapse  Enter Select  Esc Cancel")));
}
