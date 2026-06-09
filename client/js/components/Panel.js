// ── frontend/components/Panel.js ─── File panel with all view modes ─────────
const { useEffect, useRef } = React;
const h = React.createElement;
import { fmtSize, fmtDate, fileColor, toWinPath } from "../lib/utils.js";

const symName = (item) =>
  item.name === ".." ? "\u2191.."
    : item.name === "." ? "[.]"
    : item.is_dir ? `[${item.name}]${item.is_symlink ? "@" : ""}`
    : `${item.name}${item.is_symlink ? "@" : ""}`;

// ── Brief listing (multi-column CSS) ────────────────────────────────────────
function briefListing(items, selectedIdx, active, selected, onSelect, onNavigate) {
  return h("div", { style: { columnWidth: 120, columnGap: 0, columnRule: "1px solid #003366", padding: "2px 0", fontSize: 12 } },
    items.map((item, i) => {
      const isCurrent = active && i === selectedIdx;
      const isSel = selected.has(item.path);
      let color = fileColor(item);
      if (item._isParent) color = "#FFF";
      if (isSel) color = "#FFFF00";
      const cls = isCurrent ? "panel-row-current" : "";
      return h("div", {
        key: item.path || i, "data-idx": i, className: cls,
        onClick: () => onSelect(i), onDoubleClick: () => onNavigate(item),
        style: { padding: "1px 4px", cursor: "pointer", color: isCurrent ? "#000" : color, background: isCurrent ? "#00AAAA" : "transparent", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },
      }, isSel && !isCurrent ? "► " : "  ", symName(item));
    }));
}

// ── Panel component ─────────────────────────────────────────────────────────
export function Panel({ path, items, selectedIdx, active, selected, loading, error, onSelect, onActivate, onNavigate, viewMode, preview, infoData, treeNodes, treeCursor, onTreeToggle, onTreeNavigate, searchQuery }) {
  const listRef = useRef(null);

  useEffect(() => {
    if (active && listRef.current) {
      const row = listRef.current.querySelector(`[data-idx="${selectedIdx}"]`);
      if (row) row.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIdx, active]);

  const displayPath = toWinPath(path);

  return h("div", { onClick: onActivate, className: "flex-col bg-navy", style: { flex: 1, border: active ? "2px solid #00FFFF" : "2px solid #0055AA", minWidth: 0, cursor: "default" } },
    // Header
    h("div", { className: active ? "panel-header-active" : "panel-header-inactive" },
      viewMode === "search" ? `┤ Search: ${searchQuery || ""} ├` : `┤ ${displayPath} ├`),

    // Content area
    h("div", { ref: listRef, className: "scroll-y", style: { fontSize: 12 } },

      // ── Brief view ──
      viewMode === "brief" ?
        loading ? h("div", { className: "text-center text-yellow", style: { padding: "8px" } }, "Loading...") :
        error ? h("div", { className: "text-center text-red fs-11", style: { padding: "8px" } }, error) :
        briefListing(items, selectedIdx, active, selected, onSelect, onNavigate) :

      // ── Quick view ──
      viewMode === "quick" ?
        !preview ? h("div", { className: "text-center", style: { padding: "8px", color: "#555599" } }, "(no selection)") :
        preview.loading ? h("div", { className: "text-center text-yellow", style: { padding: "8px" } }, "Loading...") :
        preview.error ? h("div", { className: "text-center text-red fs-11", style: { padding: "8px" } }, preview.error) :
        h("div", { style: { padding: "4px 8px" } },
          h("div", { style: { color: "#FFFF00", marginBottom: 4 } }, preview.name),
          preview.content !== undefined ? h("pre", { style: { color: "#00FFFF", whiteSpace: "pre-wrap", wordBreak: "break-all", margin: 0, fontSize: 11, lineHeight: 1.3 } }, preview.content) :
          preview.info ? Object.entries(preview.info).filter(([k]) => !["content","name","path","modified_ts","permissions"].includes(k)).map(([k, v]) =>
            h("div", { key: k, style: { display: "flex", marginBottom: 1 } },
              h("span", { style: { color: "#FFFF00", width: 100, flexShrink: 0, fontSize: 11 } }, `${k}:`),
              h("span", { style: { color: "#00FFFF", fontSize: 11, wordBreak: "break-all" } }, typeof v === "object" ? JSON.stringify(v) : String(v)))) :
          null) :

      // ── Info view ──
      viewMode === "info" ?
        !infoData ? h("div", { className: "text-center", style: { padding: "8px", color: "#555599" } }, "(no data)") :
        infoData.loading ? h("div", { className: "text-center text-yellow", style: { padding: "8px" } }, "Loading...") :
        infoData.error ? h("div", { className: "text-center text-red fs-11", style: { padding: "8px" } }, infoData.error) :
        h("div", { style: { padding: "4px 8px", fontSize: 11, lineHeight: 1.5 } },
          [["Name", infoData.name || infoData.path],
           ["Type", infoData.is_dir ? "Directory" : "File"],
           infoData.extension ? ["Extension", infoData.extension] : null,
           !infoData.is_dir ? ["Size", fmtSize(infoData.size)] : null,
           infoData.is_dir ? ["Directories", String(infoData.dir_count ?? "?")] : null,
           infoData.is_dir ? ["Files", String(infoData.file_count ?? "?")] : null,
           infoData.is_dir ? ["Total Size", fmtSize(infoData.total_size ?? 0)] : null,
           ["Modified", new Date(infoData.modified).toLocaleString()],
           ["Created", new Date(infoData.created).toLocaleString()],
           ["Owner", infoData.owner || `${infoData.owner_uid}:${infoData.owner_gid}`],
           ["Permissions", infoData.permissions],
           ["Path", infoData.absolute_path],
           infoData.md5 ? ["MD5", infoData.md5] : null,
           infoData.disk_free ? ["Disk Free", fmtSize(infoData.disk_free)] : null,
           infoData.disk_total ? ["Disk Total", fmtSize(infoData.disk_total)] : null,
           infoData.disk_percent_used != null ? ["Disk Used", `${infoData.disk_percent_used}%`] : null,
          ].filter(Boolean).map(([k, v]) =>
            h("div", { key: k, style: { display: "flex", marginBottom: 2 } },
              h("span", { style: { color: "#FFFF00", width: 90, flexShrink: 0 } }, `${k}:`),
              h("span", { style: { color: "#00FFFF", wordBreak: "break-all" } }, String(v))))) :

      // ── Tree view ──
      viewMode === "tree" ?
        treeNodes.length === 0 ? h("div", { className: "text-center", style: { padding: "8px", color: "#555599" } }, "(loading...)") :
        h("div", { style: { padding: "2px 0", fontSize: 12 } },
          treeNodes.map((node, i) => {
            const isCurrent = active && treeCursor === i;
            return h("div", {
              key: node.path || i, "data-idx": i,
              style: { display: "flex", cursor: "pointer", color: isCurrent ? "#000" : "#FFFFFF", background: isCurrent ? "#00AAAA" : "transparent", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontFamily: '"Lucida Console", "Courier New", monospace', padding: "1px 0" },
            },
              h("span", { style: { flexShrink: 0, width: node.depth * 16 } }),
              h("span", { onClick: (ev) => { ev.stopPropagation(); onTreeToggle(node); }, style: { flexShrink: 0, width: 20, cursor: "pointer", color: "#AAAAAA" } }, node.expanded ? "[-]" : node.loading ? " ⟳" : "[+]"),
              h("span", { onClick: () => onTreeNavigate(node.path), style: { flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } }, node.name));
          })) :

      // ── Search view ──
      viewMode === "search" ?
        loading ? h("div", { className: "text-center text-yellow", style: { padding: "8px" } }, "Searching...") :
        error ? h("div", { className: "text-center text-red fs-11", style: { padding: "8px" } }, error) :
        items.length === 0 ? h("div", { className: "text-center", style: { padding: "20px", color: "#555599" } }, "No results") :
        h("table", { className: "nc-table" },
          h("thead", null,
            h("tr", { className: "text-yellow", style: { background: "#000070" } },
              h("th", { className: "nc-th" }, "Name"),
              h("th", { className: "nc-th" }, "Path"),
              h("th", { className: "nc-th text-right", style: { width: 75 } }, "Size"),
              h("th", { className: "nc-th text-right", style: { width: 140 } }, "Modified"))),
          h("tbody", null,
            items.map((item, i) => {
              const isCurrent = active && i === selectedIdx;
              const displayName = symName(item);
              const dirPath = item._isParent ? "" : item.path.substring(0, item.path.lastIndexOf("/")) || "/";
              return h("tr", {
                key: item.path || i, "data-idx": i,
                onClick: () => onSelect(i), onDoubleClick: () => onNavigate(item),
                className: "panel-row",
                style: { background: isCurrent ? "#00AAAA" : "transparent", color: isCurrent ? "#000" : "#00FFFF" },
              },
                h("td", { className: "truncate", style: { padding: "2px 6px" } }, displayName),
                h("td", { className: "truncate", style: { padding: "2px 6px", color: "#888", fontSize: 10 } }, dirPath),
                h("td", { className: "text-right filesize", style: { width: 75 } }, item._isParent ? "" : item.is_dir ? "<DIR>" : fmtSize(item.size)),
                h("td", { className: "text-right datetime", style: { width: 140 } }, item._isParent ? "" : fmtDate(item.modified)));
            }))) :

      // ── Full view (table — default) ──
      h("table", { className: "nc-table" },
        h("thead", null,
          h("tr", { className: "text-yellow", style: { background: "#000070" } },
            h("th", { className: "nc-th" }, "Name"),
            h("th", { className: "nc-th text-right", style: { width: 75 } }, "Size"),
            h("th", { className: "nc-th text-right", style: { width: 140 } }, "Modified"))),
        h("tbody", null,
          loading && h("tr", null, h("td", { colSpan: 3, className: "text-center", style: { padding: "8px", color: "#FFFF00" } }, "Loading...")),
          error && h("tr", null, h("td", { colSpan: 3, className: "text-center", style: { padding: "8px", color: "#FF5555", fontSize: 11 } }, error)),
          !loading && items.map((item, i) => {
            const isCurrent = active && i === selectedIdx;
            const isSel = selected.has(item.path);
            let color = fileColor(item);
            if (item._isParent) color = "#FFF";
            if (isSel) color = "#FFFF00";
            return h("tr", {
              key: item.path || i, "data-idx": i,
              onClick: () => onSelect(i), onDoubleClick: () => onNavigate(item),
              className: "panel-row",
              style: { background: isCurrent ? "#00AAAA" : "transparent", color: isCurrent ? "#000" : color },
            },
              h("td", { style: { padding: "2px 6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" } },
                isSel && !isCurrent ? "► " : "  ", symName(item)),
              h("td", { className: "text-right filesize", style: { width: 75 } }, item._isParent ? item.name === "." ? "ROOT" : "UP--DIR" : item.is_dir ? "<DIR>" : fmtSize(item.size)),
              h("td", { className: "text-right datetime", style: { width: 140 } }, item._isParent ? "" : fmtDate(item.modified)));
          })))),

    // Footer
    h("div", { className: "text-center", style: { borderTop: "1px solid #0055AA", padding: "2px 8px", fontSize: 11, color: "#00AAAA" } },
      viewMode === "quick" ? "Quick View" :
      viewMode === "info" ? "Info" :
      viewMode === "tree" ? `Tree ${treeNodes.length} dirs` :
      viewMode === "search" ? `${items.length} matches` :
      `${items.filter((i) => !i._isParent).length} items${selected.size > 0 ? ` │ ${selected.size} selected` : ""}`));
}
