// ── client/js/app.js ─── WebNC main component ───────────────────────────────
const { useState, useEffect, useRef, useCallback } = React;
const h = React.createElement;

import { MONO, fmtSize, fmtDate, toWinPath, fileColor, fnmatch, isArchive, isImage, isMarkdown, mdToHtml } from "./lib/utils.js";

import { api, apiList, apiView, apiCopy, apiMove, apiRename, apiMkdir, apiDelete, apiBatchDelete, apiSearch, apiDisk, apiInfo, apiDrives, apiTree, apiArchiveList, pollOperation, getToken, setToken, logout, setLogoutCallback, ncConfig, updateConfig, apiGetConfig, apiExec, apiLink } from "./lib/api.js";
import { loadConfig, saveConfig } from "./lib/config.js";
import { Panel } from "./components/Panel.js";
import { FileViewer, ConfirmDialog, InputDialog, AlertDialog, LoginDialog, DriveDialog, InfoDialog, SysInfoDialog, CompareDialog, SyncDialog, HistoryDialog, SearchDialog, ConfigDialog, TimeoutsDialog, HelpDialog, ArchiveDialog, EditorDialog, TreeDialog } from "./dialogs/index.js";

export function NortonCommander() {
  // ── Panel state ───────────────────────────────────────────────────────────
  const [leftPath, setLeftPath] = useState("/C/");
  const [rightPath, setRightPath] = useState("/C/");
  const [leftItems, setLeftItems] = useState([]);
  const [rightItems, setRightItems] = useState([]);
  const [leftIdx, setLeftIdx] = useState(0);
  const [rightIdx, setRightIdx] = useState(0);
  const [leftLoading, setLeftLoading] = useState(false);
  const [rightLoading, setRightLoading] = useState(false);
  const [leftError, setLeftError] = useState(null);
  const [rightError, setRightError] = useState(null);
  const [leftSelected, setLeftSelected] = useState(new Set());
  const [rightSelected, setRightSelected] = useState(new Set());
  const [activePanel, setActivePanel] = useState("left");

  // ── Dialogs ───────────────────────────────────────────────────────────────
  const [viewer, setViewer] = useState(null);
  const [editorDlg, setEditorDlg] = useState(null);
  const [dialog, setDialog] = useState(null);
  const [alertDlg, setAlertDlg] = useState(null);
  const [inputDlg, setInputDlg] = useState(null);
  const [infoDlg, setInfoDlg] = useState(null);
  const [driveDlg, setDriveDlg] = useState(null);
  const [searchDlg, setSearchDlg] = useState(null);
  const [sysInfoDlg, setSysInfoDlg] = useState(null);
  const [compareDlg, setCompareDlg] = useState(null);
  const [syncDlg, setSyncDlg] = useState(null);
  const [syncPlan, setSyncPlan] = useState(null);
  const [syncActions, setSyncActions] = useState([]);
  const [drivesList, setDrivesList] = useState([]);
  const [openMenu, setOpenMenu] = useState(null);
  const [statusMsg, setStatusMsg] = useState("Connecting...");
  const [diskInfo, setDiskInfo] = useState(null);
  const [connected, setConnected] = useState(false);
  const [appVersion, setAppVersion] = useState("");

  // ── Per-panel state ───────────────────────────────────────────────────────
  const [leftSortBy, setLeftSortBy] = useState("name");
  const [leftSortDir, setLeftSortDir] = useState("asc");
  const [rightSortBy, setRightSortBy] = useState("name");
  const [rightSortDir, setRightSortDir] = useState("asc");
  const [leftViewMode, setLeftViewMode] = useState("full");
  const [rightViewMode, setRightViewMode] = useState("full");
  const [leftFilter, setLeftFilter] = useState("*");
  const [rightFilter, setRightFilter] = useState("*");
  const [leftHistory, setLeftHistory] = useState(["/C/"]);
  const [rightHistory, setRightHistory] = useState(["/C/"]);
  const [historyDlg, setHistoryDlg] = useState(null);
  const [leftPreview, setLeftPreview] = useState(null);
  const [rightPreview, setRightPreview] = useState(null);
  const [leftSearchQuery, setLeftSearchQuery] = useState(null);
  const [rightSearchQuery, setRightSearchQuery] = useState(null);
  const [leftPanelVisible, setLeftPanelVisible] = useState(true);
  const [rightPanelVisible, setRightPanelVisible] = useState(true);
  const bothVisible = leftPanelVisible || rightPanelVisible;
  const [leftInfoData, setLeftInfoData] = useState(null);
  const [rightInfoData, setRightInfoData] = useState(null);
  const [leftTreeNodes, setLeftTreeNodes] = useState([]);
  const [rightTreeNodes, setRightTreeNodes] = useState([]);
  const [leftTreeCursor, setLeftTreeCursor] = useState(0);
  const [rightTreeCursor, setRightTreeCursor] = useState(0);
  const [leftTreeLoaded, setLeftTreeLoaded] = useState(new Set());
  const [config, setConfig] = useState(() => { const c = loadConfig(); updateConfig({ showHidden: c.showHidden }); return c; });
  const [configDlg, setConfigDlg] = useState(null);
  const [timeoutsDlg, setTimeoutsDlg] = useState(null);
  const [fullscreen, setFullscreen] = useState(!!document.fullscreenElement);
  const [cmdLine, setCmdLine] = useState("");
  const loadHistoryTexts = () => { try { const h = JSON.parse(localStorage.getItem("cmdHistory") || "[]"); return Array.isArray(h) ? h.slice(-100) : []; } catch { return []; } };
  const [cmdHistory, setCmdHistory] = useState([]);
  const [cmdHistoryTexts, setCmdHistoryTexts] = useState(loadHistoryTexts);
  const [cmdHistoryIdx, setCmdHistoryIdx] = useState(-1);
  const termRef = useRef(null);
  useEffect(() => { if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight; }, [cmdHistory]);
  const [keyBindings, setKeyBindings] = useState({
    "F1":"help","F2":"menu_left","F3":"view","F4":"edit","F5":"copy","F6":"move","F7":"mkdir","F8":"delete","F9":"search","F10":"quit","F11":"fullscreen",
    "Enter":"navigate","Tab":"switch_panel","Insert":"select","+":"select_group","-":"deselect_group","*":"invert_selection","Backspace":"go_up",
    "ArrowUp":"up","ArrowDown":"down","Home":"home","End":"end","PageUp":"page_up","PageDown":"page_down"
  });
  const [associations, setAssociations] = useState({});
  const [activeTarget, setActiveTarget] = useState("panels");
  const [treeDlg, setTreeDlg] = useState(null);
  const [helpDlg, setHelpDlg] = useState(null);
  const [archiveDlg, setArchiveDlg] = useState(null);
  const [loginDlg, setLoginDlg] = useState(null);
  const [loginError, setLoginError] = useState(null);

  // ── Auth callbacks ────────────────────────────────────────────────────────
  useEffect(() => {
    setLogoutCallback(() => { setLoginError(null); setLoginDlg(true); });
    return () => setLogoutCallback(null);
  }, []);

  useEffect(() => { if (!getToken()) setLoginDlg(true); }, []);

  const handleLogin = (token) => { setToken(token); setLoginDlg(null); setLoginError(null); setStatusMsg(""); };
  const handleLogout = () => { logout(); setLoginError(null); setLoginDlg(true); };

  // ── History tracking ──────────────────────────────────────────────────────
  useEffect(() => { if (leftPath !== leftHistory[leftHistory.length - 1]) setLeftHistory((p) => { const n = [...p, leftPath]; return n.length > 50 ? n.slice(-50) : n; }); }, [leftPath]);
  useEffect(() => { if (rightPath !== rightHistory[rightHistory.length - 1]) setRightHistory((p) => { const n = [...p, rightPath]; return n.length > 50 ? n.slice(-50) : n; }); }, [rightPath]);

  // ── Fetch directory listing ───────────────────────────────────────────────
  const fetchDir = useCallback(async (path, side, optBy, optDir, optFilter) => {
    const setItems = side === "left" ? setLeftItems : setRightItems;
    const setLoading = side === "left" ? setLeftLoading : setRightLoading;
    const setError = side === "left" ? setLeftError : setRightError;
    const setIdx = side === "left" ? setLeftIdx : setRightIdx;
    const setSel = side === "left" ? setLeftSelected : setRightSelected;
    setLoading(true); setError(null);
    try {
      const sb = optBy || (side === "left" ? leftSortBy : rightSortBy);
      const sd = optDir || (side === "left" ? leftSortDir : rightSortDir);
      const fl = optFilter || (side === "left" ? leftFilter : rightFilter);
      const data = await apiList(path, sb, sd, fl);
      const items = [];
      items.push({ name: ".", path: data.path, is_dir: true, size: 0, modified: "", extension: "", _isParent: true });
      if (data.parent !== null && data.parent !== undefined) items.push({ name: "..", path: data.parent, is_dir: true, size: 0, modified: "", extension: "", _isParent: true });
      items.push(...data.items.map((i) => ({ ...i, _isParent: false })));
      setItems(items); setIdx(0); setSel(new Set());
    } catch (e) { setError(e.message); setItems([]); }
    finally { setLoading(false); }
  }, [leftSortBy, rightSortBy, leftSortDir, rightSortDir, leftFilter, rightFilter]);

  // ── Initial load ──────────────────────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const health = await api("GET", "/api/health");
        setAppVersion(health.version || "");
        setConnected(true); setStatusMsg("Ready");
        const disk = await apiDisk("/C/"); setDiskInfo(disk);
        setLeftSortBy(config.defaultSortBy); setLeftSortDir(config.defaultSortDir);
        setRightSortBy(config.defaultSortBy); setRightSortDir(config.defaultSortDir);
        setLeftViewMode(config.defaultView); setRightViewMode(config.defaultView);
        fetchDir("/C/", "left", config.defaultSortBy, config.defaultSortDir);
        fetchDir("/C/", "right", config.defaultSortBy, config.defaultSortDir);
      } catch { setConnected(false); setStatusMsg("Cannot connect. Start: python nc_server.py"); }
    })();
  }, [config]);

  // ── Active panel helpers ──────────────────────────────────────────────────
  const cur = activePanel === "left"
    ? { items: leftItems, idx: leftIdx, path: leftPath, setIdx: setLeftIdx, setPath: setLeftPath, selected: leftSelected, setSelected: setLeftSelected }
    : { items: rightItems, idx: rightIdx, path: rightPath, setIdx: setRightIdx, setPath: setRightPath, selected: rightSelected, setSelected: setRightSelected };
  const opp = activePanel === "left" ? { path: rightPath, fetchDir: () => fetchDir(rightPath, "right") } : { path: leftPath, fetchDir: () => fetchDir(leftPath, "left") };
  const refreshBoth = () => { fetchDir(leftPath, "left"); fetchDir(rightPath, "right"); };
  const dispatchKey = (key) => window.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
  const swapPanels = () => { const nl = rightPath, nr = leftPath; setLeftPath(nl); setRightPath(nr); fetchDir(nl, "left"); fetchDir(nr, "right"); };
  const toggleFullscreen = () => { if (!document.fullscreenElement) { document.documentElement.requestFullscreen(); setFullscreen(true); } else { document.exitFullscreen(); setFullscreen(false); } };
  const searchNavigate = (r) => { if (r.is_dir) { navigate(r, activePanel); } else { const p = r.path.substring(0, r.path.lastIndexOf("/")) || "/C/"; if (activePanel === "left") setLeftPath(p); else setRightPath(p); fetchDir(p, activePanel); } };
  const handleSearchResults = (results, query, truncated) => {
    const otherSide = activePanel === "left" ? "right" : "left";
    const setViewMode = otherSide === "left" ? setLeftViewMode : setRightViewMode;
    const setItems = otherSide === "left" ? setLeftItems : setRightItems;
    const setIdx = otherSide === "left" ? setLeftIdx : setRightIdx;
    const setSel = otherSide === "left" ? setLeftSelected : setRightSelected;
    const setSearchQ = otherSide === "left" ? setLeftSearchQuery : setRightSearchQuery;
    setSearchQ(`${query}${truncated ? " (truncated)" : ""}`);
    setItems(results.map((r) => ({ ...r, _isParent: false })));
    setViewMode("search");
    setIdx(0);
    setSel(new Set());
    setActivePanel(otherSide);
  };

  // ── Sort / view / info handlers ───────────────────────────────────────────
  const handleSort = (field, side) => {
    const setBy = side === "left" ? setLeftSortBy : setRightSortBy;
    const setDir = side === "left" ? setLeftSortDir : setRightSortDir;
    const curBy = side === "left" ? leftSortBy : rightSortBy;
    const curDir = side === "left" ? leftSortDir : rightSortDir;
    const path = side === "left" ? leftPath : rightPath;
    let newBy, newDir;
    if (field === "unsorted") { newBy = "unsorted"; newDir = "asc"; }
    else if (field === curBy) { newBy = field; newDir = curDir === "asc" ? "desc" : "asc"; }
    else { newBy = field; newDir = "asc"; }
    setBy(newBy); setDir(newDir); fetchDir(path, side, newBy, newDir);
  };
  const handleViewMode = (mode, side) => {
    const curMode = side === "left" ? leftViewMode : rightViewMode;
    if (curMode === "search" && mode !== "search") {
      const path = side === "left" ? leftPath : rightPath;
      fetchDir(path, side);
    }
    (side === "left" ? setLeftViewMode : setRightViewMode)(mode);
  };
  const handleDirInfo = async (side) => { try { setInfoDlg(await apiInfo(side === "left" ? leftPath : rightPath)); } catch (err) { setAlertDlg({ message: `Info error: ${err.message}` }); } };

  const handleEditorSave = async (path, content) => {
    await api("POST", "/api/edit", { path, content });
    setStatusMsg("File saved");
  };

  const handleCmdEnter = async () => {
    const cmd = cmdLine.trim();
    if (!cmd) return;
    setCmdLine("");
    setCmdHistoryIdx(-1);
    setStatusMsg(`Executing: ${cmd}`);
    setCmdHistoryTexts((prev) => { const n = [...prev, cmd].slice(-100); localStorage.setItem("cmdHistory", JSON.stringify(n)); return n; });
    try {
      const res = await apiExec(cmd, activePanel === "left" ? leftPath : rightPath);
      const out = [res.stdout, res.stderr].filter(Boolean).join("\n").trim();
      setCmdHistory((prev) => [...prev, { cmd, stdout: out, returncode: res.returncode }]);
      setStatusMsg(`Done (exit code ${res.returncode})`);
    } catch (err) {
      setCmdHistory((prev) => [...prev, { cmd, stdout: err.message, returncode: -1 }]);
      setAlertDlg({ message: `Exec error: ${err.message}` });
    }
  };

  const handleCompressedFile = (side, password) => {
    const items = side === "left" ? leftItems : rightItems;
    const idx = side === "left" ? leftIdx : rightIdx;
    const item = items[idx];
    if (!item || item._isParent || item.is_dir) { setStatusMsg("Select a compressed file first"); return; }
    if (!isArchive(item.name)) { setStatusMsg("Not a compressed file"); return; }
    const doOpen = async (pw) => {
      setArchiveDlg({ path: item.path, name: item.name, loading: true, password: pw });
      try {
        const data = await apiArchiveList(item.path, pw);
        setArchiveDlg({ path: item.path, name: item.name, data, loading: false, password: pw });
      } catch (err) {
        if (err.message && (err.message.includes("Password") || err.message.includes("password"))) {
          setArchiveDlg(null);
          setInputDlg({ title: "Archive Password", label: `Password for ${item.name}:`, defaultValue: "", onOk: (p) => { setInputDlg(null); handleCompressedFile(side, p); }, onCancel: () => setInputDlg(null) });
        } else { setArchiveDlg({ path: item.path, name: item.name, error: err.message, loading: false, password: pw }); }
      }
    };
    doOpen(password || "");
  };

  // ── Selection handlers ────────────────────────────────────────────────────
  const handleSelectGroup = (side) => {
    const items = side === "left" ? leftItems : rightItems;
    setInputDlg({ title: "Select Group", label: "Enter file pattern to select:", defaultValue: "*.*",
      onOk: (pat) => { setInputDlg(null); const setSel = side === "left" ? setLeftSelected : setRightSelected; setSel((prev) => { const n = new Set(prev); items.forEach((i) => { if (!i._isParent && fnmatch(pat, i.name)) n.add(i.path); }); return n; }); setStatusMsg(`Selected: ${items.filter((i) => !i._isParent && fnmatch(pat, i.name)).length} item(s)`); },
      onCancel: () => setInputDlg(null) });
  };
  const handleDeselectGroup = (side) => {
    const items = side === "left" ? leftItems : rightItems;
    setInputDlg({ title: "Deselect Group", label: "Enter file pattern to deselect:", defaultValue: "*.*",
      onOk: (pat) => { setInputDlg(null); const setSel = side === "left" ? setLeftSelected : setRightSelected; setSel((prev) => { const n = new Set(prev); items.forEach((i) => { if (!i._isParent && fnmatch(pat, i.name)) n.delete(i.path); }); return n; }); setStatusMsg(`Deselected: ${items.filter((i) => !i._isParent && fnmatch(pat, i.name)).length} item(s)`); },
      onCancel: () => setInputDlg(null) });
  };
  const handleInvertSelection = (side) => { const items = side === "left" ? leftItems : rightItems; const setSel = side === "left" ? setLeftSelected : setRightSelected; setSel((prev) => { const n = new Set(prev); items.forEach((i) => { if (!i._isParent) { n.has(i.path) ? n.delete(i.path) : n.add(i.path); } }); return n; }); setStatusMsg("Selection inverted"); };

  // ── Tree handlers ─────────────────────────────────────────────────────────
  const loadTreeRoot = async (side) => {
    const path = side === "left" ? leftPath : rightPath;
    const letter = path.match(/^\/([A-Z])\//)?.[1] || "C";
    const rootPath = `/${letter}/`;
    const setNodes = side === "left" ? setLeftTreeNodes : setRightTreeNodes;
    const setCursor = side === "left" ? setLeftTreeCursor : setRightTreeCursor;
    const setLoaded = side === "left" ? setLeftTreeLoaded : setRightTreeLoaded;
    try {
      const data = await apiTree(rootPath);
      const root = { name: `${letter}:\\`, path: rootPath, depth: 0, expanded: true, loading: false };
      const children = data.dirs.map((d) => ({ ...d, depth: 1, expanded: false, loading: false }));
      setNodes([root, ...children]); setCursor(0); setLoaded(new Set([rootPath]));
      treeNavigateOpposite(side, rootPath);
    } catch (err) { setAlertDlg({ message: `Tree error: ${err.message}` }); }
  };
  const expandTreeNode = async (side, node) => {
    if (node.loading) return;
    const setNodes = side === "left" ? setLeftTreeNodes : setRightTreeNodes;
    const setLoaded = side === "left" ? setLeftTreeLoaded : setRightTreeLoaded;
    setNodes((prev) => prev.map((n) => n.path === node.path ? { ...n, expanded: true, loading: true } : n));
    try {
      const data = await apiTree(node.path);
      const children = data.dirs.map((d) => ({ ...d, depth: node.depth + 1, expanded: false, loading: false }));
      setNodes((prev) => { const idx = prev.findIndex((n) => n.path === node.path); if (idx === -1) return prev; return [...prev.slice(0, idx + 1), ...children, ...prev.slice(idx + 1)].map((n) => n.path === node.path ? { ...n, loading: false, expanded: true } : n); });
      setLoaded((prev) => new Set(prev).add(node.path));
    } catch (err) { setNodes((prev) => prev.map((n) => n.path === node.path ? { ...n, loading: false } : n)); setAlertDlg({ message: `Tree expand error: ${err.message}` }); }
  };
  const collapseTreeNode = (side, node) => {
    const setNodes = side === "left" ? setLeftTreeNodes : setRightTreeNodes;
    setNodes((prev) => { const idx = prev.findIndex((n) => n.path === node.path); if (idx === -1) return prev; return prev.slice(0, idx + 1).map((n) => n.path === node.path ? { ...n, expanded: false } : n).concat(prev.slice(idx + 1).filter((n) => n.depth <= node.depth)); });
  };
  const toggleTreeNode = (side, node) => { if (!node) return; node.expanded ? collapseTreeNode(side, node) : expandTreeNode(side, node); };
  const treeNavigateOpposite = (side, treePath) => { if (!treePath) return; if (side === "left") { setRightPath(treePath); fetchDir(treePath, "right"); } else { setLeftPath(treePath); fetchDir(treePath, "left"); } };

  // ── Commands menu handlers ────────────────────────────────────────────────
  const handleSystemInfo = async () => { try { setSysInfoDlg(await api("GET", "/api/sysinfo")); } catch (err) { setAlertDlg({ message: `SysInfo error: ${err.message}` }); } };

  const handleLink = () => {
    const side = activePanel;
    const items = side === "left" ? leftItems : rightItems;
    const idx = side === "left" ? leftIdx : rightIdx;
    const item = items[idx];
    const currentPath = side === "left" ? leftPath : rightPath;
    const oppPath = side === "left" ? rightPath : leftPath;
    if (!item || item._isParent) return;
    setInputDlg({
      title: "Create Symbolic Link",
      label: `Link target: ${item.name} (from ${toWinPath(currentPath)})\nEnter link name in ${toWinPath(oppPath)}:`,
      defaultValue: item.name,
      onOk: async (name) => { setInputDlg(null); try { await apiLink(item.path, `${oppPath.replace(/\/$/, "")}/${name}`); setStatusMsg(`Linked ${item.name} \u2192 ${name}`); fetchDir(oppPath, side === "left" ? "right" : "left"); } catch (err) { setAlertDlg({ message: err.message }); } },
      onCancel: () => setInputDlg(null),
    });
  };

  const handleCompare = async () => { try { const { operation_id, poll } = await api("POST", "/api/compare", { left: leftPath, right: rightPath }); setCompareDlg(await pollOperation(operation_id, poll?.timeout, poll?.interval)); } catch (err) { setAlertDlg({ message: `Compare error: ${err.message}` }); } };
  const compareNavigate = (item, side) => { if (!item || !item.path) return; const setPath = side === "left" ? setLeftPath : setRightPath; if (item.is_dir) { setPath(item.path); fetchDir(item.path, side); } else { const pp = item.path.substring(0, item.path.lastIndexOf("/")) || "/C/"; setPath(pp); fetchDir(pp, side); } };
  const handleSync = () => { setSyncPlan(null); setSyncActions([]); setSyncDlg("setup"); };
  const handleSyncCompare = async (opts) => {
    setStatusMsg("Comparing...");
    try {
      const { operation_id, poll } = await api("POST", "/api/sync/plan", { left: leftPath, right: rightPath, subdirs: opts.subdirs, by_content: opts.byContent, ignore_date: opts.ignoreDate, asymmetric: opts.asymmetric, filter: opts.filter || "*" });
      const plan = await pollOperation(operation_id, poll?.timeout, poll?.interval);
      const defaultActions = []; plan.forEach((item) => { if (item.suggested) defaultActions.push({ name: item.path, action: item.suggested }); });
      setSyncPlan(plan); setSyncActions(defaultActions); setSyncDlg("plan"); setStatusMsg("Ready");
    } catch (err) { setAlertDlg({ message: `Sync error: ${err.message}` }); }
  };
  const syncExecute = async () => {
    if (!syncActions.length) { setStatusMsg("No items selected to sync"); return; }
    try { const { operation_id, poll } = await api("POST", "/api/sync/execute", { left: leftPath, right: rightPath, actions: syncActions }); const result = await pollOperation(operation_id, poll?.timeout, poll?.interval); setSyncDlg("result"); setSyncPlan(result); } catch (err) { setAlertDlg({ message: `Sync execute error: ${err.message}` }); }
  };
  const syncToggleItem = (path, action) => { setSyncActions((prev) => { if (!action) return prev.filter((a) => a.name !== path); const idx = prev.findIndex((a) => a.name === path); if (idx >= 0) { const u = [...prev]; u[idx] = { name: path, action }; return u; } return [...prev, { name: path, action }]; }); };
  const syncSetAll = (on) => { if (!syncPlan || !syncPlan.length) return; if (!on) { setSyncActions([]); return; } const result = []; syncPlan.forEach((item) => { if (item.suggested) result.push({ name: item.path, action: item.suggested }); }); setSyncActions(result); };
  const handleHistory = () => setHistoryDlg(activePanel === "left" ? leftHistory : rightHistory);

  // ── Navigate ──────────────────────────────────────────────────────────────
  const navigate = useCallback(async (item, side) => {
    const setPath = side === "left" ? setLeftPath : setRightPath;
    const curMode = side === "left" ? leftViewMode : rightViewMode;
    const setViewMode = side === "left" ? setLeftViewMode : setRightViewMode;
    if (item._isParent || item.is_dir) {
      if (curMode === "search") setViewMode("full");
      setPath(item.path); fetchDir(item.path, side);
    } else {
      if (curMode === "search") setViewMode("full");
      const ext = item.extension ? "." + item.extension.toLowerCase() : "";
      const action = associations[ext];
      if (action === "edit") {
        try { const v = await apiView(item.path, true); setEditorDlg({ filename: item.name, content: v.content, path: item.path }); } catch (err) { setAlertDlg({ message: `Edit error: ${err.message}` }); }
      } else if (action === "archive") {
        const doOpen = async (pw) => { setArchiveDlg({ path: item.path, name: item.name, loading: true, password: pw }); try { const data = await apiArchiveList(item.path, pw); setArchiveDlg({ path: item.path, name: item.name, data, loading: false, password: pw }); } catch (err) { if (err.message && err.message.includes("password")) { setArchiveDlg(null); setInputDlg({ title: "Archive Password", label: `Password for ${item.name}:`, defaultValue: "", onOk: (p) => { setInputDlg(null); doOpen(p); }, onCancel: () => setInputDlg(null) }); } else { setAlertDlg({ message: err.message }); } } }; doOpen();
      } else if (isImage(item.name)) {
        setViewer({ filename: item.name, type: "image", src: "", loading: true });
        try { const tok = getToken(); const r = await fetch(`/api/download?path=${encodeURIComponent(item.path)}`, { headers: tok ? { "X-Session-Token": tok } : {} }); if (!r.ok) throw new Error("Download failed"); const blob = await r.blob(); const url = URL.createObjectURL(blob); setViewer({ filename: item.name, type: "image", src: url, loading: false }); } catch (err) { setAlertDlg({ message: `Preview error: ${err.message}` }); }
      } else if (isMarkdown(item.name)) {
        setViewer({ filename: item.name, type: "html", content: "", loading: true });
        try { const v = await apiView(item.path); setViewer({ filename: item.name, type: "html", content: mdToHtml(v.content), loading: false }); } catch (err) { setAlertDlg({ message: `View error: ${err.message}` }); }
      } else {
        setViewer({ filename: item.name, content: "", loading: true }); try { const data = await apiView(item.path); setViewer({ filename: item.name, content: data.content, loading: false }); } catch (e) { setViewer({ filename: item.name, content: `Error: ${e.message}`, loading: false }); }
      }
    }
  }, [fetchDir, leftViewMode, rightViewMode, associations, apiView, apiArchiveList]);

  // ── Preview (quick view) ──────────────────────────────────────────────────
  const fetchPreview = useCallback(async (side) => {
    const isQuick = side === "left" ? leftViewMode === "quick" : rightViewMode === "quick";
    if (!isQuick) return;
    const oppIdx = side === "left" ? rightIdx : leftIdx;
    const oppItems = side === "left" ? rightItems : leftItems;
    const item = oppItems[oppIdx];
    if (!item || item._isParent) { (side === "left" ? setLeftPreview : setRightPreview)(null); return; }
    const setPreview = side === "left" ? setLeftPreview : setRightPreview;
    setPreview({ name: item.name, loading: true, content: undefined, info: undefined });
    try {
      if (item.is_dir) { setPreview({ name: item.name, loading: false, info: await apiInfo(item.path) }); }
      else { const info = await apiInfo(item.path); let content; if (item.size < 65536) { try { const v = await apiView(item.path); content = v.content; } catch { content = undefined; } } setPreview({ name: item.name, loading: false, info, content }); }
    } catch (e) { setPreview({ name: item.name, loading: false, error: e.message }); }
  }, [leftItems, rightItems, leftIdx, rightIdx, leftPath, rightPath, leftViewMode, rightViewMode]);

  useEffect(() => { if (leftViewMode !== "quick") setLeftPreview(null); else fetchPreview("left"); }, [fetchPreview, leftIdx, leftViewMode, rightViewMode]);
  useEffect(() => { if (rightViewMode !== "quick") setRightPreview(null); else fetchPreview("right"); }, [fetchPreview, rightIdx, rightViewMode, leftViewMode]);

  // ── Info view data ────────────────────────────────────────────────────────
  useEffect(() => { if (leftViewMode !== "info") { setLeftInfoData(null); return; } setLeftInfoData({ loading: true }); (async () => { try { setLeftInfoData(await apiInfo(rightPath)); } catch (e) { setLeftInfoData({ error: e.message }); } })(); }, [leftViewMode, rightPath]);
  useEffect(() => { if (rightViewMode !== "info") { setRightInfoData(null); return; } setRightInfoData({ loading: true }); (async () => { try { setRightInfoData(await apiInfo(leftPath)); } catch (e) { setRightInfoData({ error: e.message }); } })(); }, [rightViewMode, leftPath]);

  // ── Tree view init ────────────────────────────────────────────────────────
  useEffect(() => { if (leftViewMode !== "tree") { setLeftTreeNodes([]); setLeftTreeCursor(0); return; } loadTreeRoot("left"); }, [leftViewMode, rightViewMode]);
  useEffect(() => { if (rightViewMode !== "tree") { setRightTreeNodes([]); setRightTreeCursor(0); return; } loadTreeRoot("right"); }, [rightViewMode, leftViewMode]);

  // ── Status auto-clear ─────────────────────────────────────────────────────
  useEffect(() => { if (statusMsg !== "Ready" && connected) { const t = setTimeout(() => setStatusMsg("Ready"), 3500); return () => clearTimeout(t); } }, [statusMsg, connected]);

  // ── Keyboard handler ──────────────────────────────────────────────────────
  useEffect(() => {
    if (viewer || editorDlg || dialog || inputDlg || infoDlg || driveDlg || searchDlg || sysInfoDlg || compareDlg || syncDlg || historyDlg || configDlg || timeoutsDlg || helpDlg || archiveDlg || loginDlg) return;
    const handler = async (e) => {
      if (activeTarget === "terminal") return;
      if (treeDlg) return;
      const { items, idx, setIdx, path, selected, setSelected } = activePanel === "left"
        ? { items: leftItems, idx: leftIdx, setIdx: setLeftIdx, path: leftPath, selected: leftSelected, setSelected: setLeftSelected }
        : { items: rightItems, idx: rightIdx, setIdx: setRightIdx, path: rightPath, selected: rightSelected, setSelected: setRightSelected };
      const item = items[idx];
      if (e.altKey && e.key === "F1") { e.preventDefault(); setDriveDlg({ side: "left" }); return; }
      if (e.altKey && e.key === "F2") { e.preventDefault(); setDriveDlg({ side: "right" }); return; }
      const oppPath = activePanel === "left" ? rightPath : leftPath;
      const curViewMode = activePanel === "left" ? leftViewMode : rightViewMode;

      // Tree mode keys
      if (curViewMode === "tree") {
        const treeNodes = activePanel === "left" ? leftTreeNodes : rightTreeNodes;
        const treeCur = activePanel === "left" ? leftTreeCursor : rightTreeCursor;
        const setTreeCur = activePanel === "left" ? setLeftTreeCursor : setRightTreeCursor;
        const treeNode = treeNodes[treeCur];
        const moveTree = (i) => { setTreeCur(i); const n = treeNodes[i]; if (n) treeNavigateOpposite(activePanel, n.path); };
        switch (e.key) {
          case "ArrowUp": e.preventDefault(); moveTree(Math.max(0, treeCur - 1)); break;
          case "ArrowDown": e.preventDefault(); moveTree(Math.min(treeNodes.length - 1, treeCur + 1)); break;
          case "Home": e.preventDefault(); moveTree(0); break;
          case "End": e.preventDefault(); moveTree(treeNodes.length - 1); break;
          case "PageUp": e.preventDefault(); moveTree(Math.max(0, treeCur - 15)); break;
          case "PageDown": e.preventDefault(); moveTree(Math.min(treeNodes.length - 1, treeCur + 15)); break;
          case "Enter": e.preventDefault(); if (treeNode) { toggleTreeNode(activePanel, treeNode); treeNavigateOpposite(activePanel, treeNode.path); } break;
          case "Tab": e.preventDefault(); if (activeTarget === "terminal") { setActiveTarget("panels"); setActivePanel("left"); } else if (activePanel === "right") { setActiveTarget("terminal"); } else { setActivePanel((p) => (p === "left" ? "right" : "left")); } break;
          default: return;
        }
        return;
      }

      // Normal mode keys — dispatched via keyBindings config
      const actionName = keyBindings && keyBindings[e.key];
      if (!actionName) return;
      e.preventDefault();

      const ACTION = {
        up: () => setIdx(Math.max(0, idx - 1)),
        down: () => setIdx(Math.min(items.length - 1, idx + 1)),
        home: () => setIdx(0),
        end: () => setIdx(items.length - 1),
        page_up: () => setIdx(Math.max(0, idx - 15)),
        page_down: () => setIdx(Math.min(items.length - 1, idx + 15)),
        fullscreen: toggleFullscreen,
        navigate: () => { if (item) navigate(item, activePanel); },
        switch_panel: () => { if (activeTarget === "terminal") { setActiveTarget("panels"); setActivePanel("left"); } else if (activePanel === "right") { setActiveTarget("terminal"); } else { setActivePanel((p) => (p === "left" ? "right" : "left")); } },
        select: () => { if (item && !item._isParent) { setSelected((prev) => { const n = new Set(prev); n.has(item.path) ? n.delete(item.path) : n.add(item.path); return n; }); setIdx(Math.min(items.length - 1, idx + 1)); } },
        select_group: () => setInputDlg({ title: "Select Group", label: "Enter file pattern to select:", defaultValue: "*.*", onOk: (pat) => { setInputDlg(null); setSelected((prev) => { const n = new Set(prev); items.forEach((i) => { if (!i._isParent && fnmatch(pat, i.name)) n.add(i.path); }); return n; }); }, onCancel: () => setInputDlg(null) }),
        deselect_group: () => setInputDlg({ title: "Deselect Group", label: "Enter file pattern to deselect:", defaultValue: "*.*", onOk: (pat) => { setInputDlg(null); setSelected((prev) => { const n = new Set(prev); items.forEach((i) => { if (!i._isParent && fnmatch(pat, i.name)) n.delete(i.path); }); return n; }); }, onCancel: () => setInputDlg(null) }),
        invert_selection: () => setSelected((prev) => { const n = new Set(prev); items.forEach((i) => { if (!i._isParent) { n.has(i.path) ? n.delete(i.path) : n.add(i.path); } }); return n; }),
        go_up: () => navigate({ name: "..", path: path.substring(0, path.lastIndexOf("/")) || "/", is_dir: true, _isParent: true }, activePanel),
        help: () => setHelpDlg(true),
        menu_left: () => setOpenMenu((p) => (p ? null : "Left")),
        view: async () => { if (item && !item._isParent && !item.is_dir) { setViewer({ filename: item.name, content: "", loading: true }); try { const d = await apiView(item.path); setViewer({ filename: item.name, content: d.content, loading: false }); } catch (err) { setViewer({ filename: item.name, content: `Error: ${err.message}`, loading: false }); } } },
        edit: async () => { if (item && !item._isParent) { if (item.is_dir) { try { setInfoDlg(await apiInfo(item.path)); } catch (err) { setAlertDlg({ message: `Info error: ${err.message}` }); } } else { try { const v = await apiView(item.path, true); setEditorDlg({ filename: item.name, content: v.content, path: item.path }); } catch (err) { setAlertDlg({ message: `Edit error: ${err.message}` }); } } } },
        copy: () => { if (!item || item._isParent) return; const t = selected.size > 0 ? [...selected] : [item.path]; setDialog({ title: "Copy", message: `Copy ${t.length} item(s) to ${oppPath}?`, onYes: async () => { setDialog(null); try { for (const s of t) await apiCopy(s, oppPath); setStatusMsg(`Copied ${t.length} item(s)`); setSelected(new Set()); refreshBoth(); } catch (err) { setAlertDlg({ message: `Copy error: ${err.message}` }); } }, onNo: () => setDialog(null) }); },
        move: () => { if (!item || item._isParent) return; if (selected.size === 0) { setInputDlg({ title: "Move / Rename", label: `Rename "${item.name}" or move to ${oppPath}:`, defaultValue: item.name, onOk: async (n) => { setInputDlg(null); try { if (n !== item.name) { await apiRename(item.path, n); setStatusMsg(`Renamed → ${n}`); } else { await apiMove(item.path, oppPath); setStatusMsg(`Moved → ${oppPath}`); } refreshBoth(); } catch (err) { setAlertDlg({ message: `Move error: ${err.message}` }); } }, onCancel: () => setInputDlg(null) }); } else { const t = [...selected]; setDialog({ title: "Move", message: `Move ${t.length} item(s) to ${oppPath}?`, onYes: async () => { setDialog(null); try { for (const s of t) await apiMove(s, oppPath); setStatusMsg(`Moved ${t.length} item(s)`); setSelected(new Set()); refreshBoth(); } catch (err) { setAlertDlg({ message: `Move error: ${err.message}` }); } }, onNo: () => setDialog(null) }); } },
        mkdir: () => setInputDlg({ title: "Create Directory", label: `New directory in ${toWinPath(path)}:`, defaultValue: "", onOk: async (name) => { setInputDlg(null); try { await apiMkdir(`${path.replace(/\/$/, "")}/${name}`); setStatusMsg(`Created ${name}`); fetchDir(path, activePanel); } catch (err) { setAlertDlg({ message: `MkDir error: ${err.message}` }); } }, onCancel: () => setInputDlg(null) }),
        link: handleLink,
        delete: () => { if (!item || item._isParent) return; const t = selected.size > 0 ? [...selected] : [item.path]; const names = t.map((p) => p.split("/").pop()).join(", "); setDialog({ title: "Delete", message: `Delete ${t.length} item(s): ${names.substring(0, 60)}${names.length > 60 ? "..." : ""}?`, onYes: async () => { setDialog(null); try { if (t.length === 1) await apiDelete(t[0], true); else await apiBatchDelete(t, true); setStatusMsg(`Deleted ${t.length} item(s)`); setSelected(new Set()); fetchDir(path, activePanel); } catch (err) { setAlertDlg({ message: `Delete error: ${err.message}` }); } }, onNo: () => setDialog(null) }); },
        search: () => setSearchDlg({ onResults: handleSearchResults }),
        quit: handleLogout,
      };

      const fn = ACTION[actionName];
      if (fn) await fn();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [activePanel, leftItems, rightItems, leftIdx, rightIdx, leftPath, rightPath, leftSelected, rightSelected, leftViewMode, rightViewMode, leftTreeNodes, rightTreeNodes, leftTreeCursor, rightTreeCursor, viewer, editorDlg, dialog, inputDlg, infoDlg, driveDlg, searchDlg, sysInfoDlg, compareDlg, syncDlg, historyDlg, configDlg, timeoutsDlg, helpDlg, archiveDlg, loginDlg, treeDlg, leftPanelVisible, rightPanelVisible, navigate, fetchDir, toggleFullscreen, refreshBoth, handleSearchResults, handleLogout, treeNavigateOpposite, toggleTreeNode, keyBindings, apiView, apiInfo, apiCopy, apiMove, apiRename, apiMkdir, apiDelete, apiBatchDelete, setStatusMsg, setOpenMenu, setViewer, setEditorDlg, setInfoDlg, setSearchDlg, setHelpDlg, setInputDlg, setDialog, setLeftIdx, setRightIdx, setLeftSelected, setRightSelected, setLeftTreeCursor, setRightTreeCursor, setActivePanel, activeTarget]);

  // ── Fetch keybindings + associations from config ──────────────────────────
  useEffect(() => {
    apiGetConfig().then(cfg => { setKeyBindings(cfg.keybindings || {}); setAssociations(cfg.associations || {}); }).catch(() => {});
  }, []);

  // ── Ctrl+O ────────────────────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e) => { if (e.ctrlKey && (e.key === "o" || e.key === "O")) { e.preventDefault(); const newVal = !leftPanelVisible; setLeftPanelVisible(newVal); setRightPanelVisible(newVal); setActiveTarget(newVal ? "panels" : "terminal"); } };
    document.addEventListener("keydown", handler, { capture: true });
    return () => document.removeEventListener("keydown", handler, { capture: true });
  }, []);

  // ── Fullscreen change tracking ────────────────────────────────────────────
  useEffect(() => {
    const handler = () => setFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  // ── Menu close on outside click ───────────────────────────────────────────
  const menuRef = useRef(null);
  useEffect(() => { if (!openMenu) return; const handler = (e) => { if (menuRef.current && !menuRef.current.contains(e.target)) setOpenMenu(null); }; window.addEventListener("click", handler); return () => window.removeEventListener("click", handler); }, [openMenu]);

  // ── Load drives on drive dialog open ──────────────────────────────────────
  useEffect(() => { if (driveDlg) { (async () => { try { const all = await apiDrives(); setDrivesList(all.filter((d) => d.total > 0)); } catch (err) { setAlertDlg({ message: `Drives error: ${err.message}` }); setDriveDlg(null); } })(); } else setDrivesList([]); }, [driveDlg]);

  // ── Menu definitions ──────────────────────────────────────────────────────
  const menuItems = {
    "Left": [
      { label: leftViewMode === "brief" ? "  [X] Brief" : "  Brief", action: () => handleViewMode("brief", "left") },
      { label: leftViewMode === "full" ? "  [X] Full" : "  Full", action: () => handleViewMode("full", "left") },
      { label: leftViewMode === "quick" ? "  [X] Quick view" : "  Quick view", action: () => handleViewMode("quick", "left") },
      { label: leftViewMode === "info" ? "  [X] Info" : "  Info", action: () => handleViewMode("info", "left") },
      { label: leftViewMode === "tree" ? "  [X] Tree" : "  Tree", action: () => handleViewMode("tree", "left") },
      { label: "  Compressed File", action: () => handleCompressedFile("left") },
      { label: leftViewMode === "search" ? "  [X] Find file panel" : "  Find file panel", action: () => { setSearchDlg({ side: "left", onResults: handleSearchResults }); } },
      { label: "  Directory information", action: () => handleDirInfo("left") },
      { label: "  Link", disabled: true },
      { label: leftPanelVisible ? "  [X] On" : "  Off", action: () => setLeftPanelVisible((p) => !p) },
      null,
      { label: leftSortBy === "name" ? "  [X] Name" : "  Name", action: () => handleSort("name", "left") },
      { label: leftSortBy === "extension" ? "  [X] Extension" : "  Extension", action: () => handleSort("extension", "left") },
      { label: leftSortBy === "modified" ? "  [X] Time" : "  Time", action: () => handleSort("modified", "left") },
      { label: leftSortBy === "size" ? "  [X] Size" : "  Size", action: () => handleSort("size", "left") },
      { label: leftSortBy === "unsorted" ? "  [X] Unsorted" : "  Unsorted", action: () => handleSort("unsorted", "left") },
      null,
      { label: "Re-read", action: () => fetchDir(leftPath, "left") },
      { label: "Filter...", action: () => setInputDlg({ title: "Filter", label: `Enter file pattern (current: ${leftFilter === "*" ? "all files" : leftFilter}):`, defaultValue: leftFilter, onOk: (val) => { setInputDlg(null); const f = val.trim() || "*"; setLeftFilter(f); fetchDir(leftPath, "left", null, null, f); }, onCancel: () => setInputDlg(null) }) },
      { label: "Drive...", action: () => setDriveDlg({ side: "left" }) },
    ],
    "Files": [
      { label: "View", action: () => dispatchKey("F3"), shortcut: "F3" },
      { label: "Edit", action: () => dispatchKey("F4"), shortcut: "F4" },
      null,
      { label: "Select Group", action: () => handleSelectGroup(activePanel), shortcut: "+" },
      { label: "Deselect Group", action: () => handleDeselectGroup(activePanel), shortcut: "−" },
      { label: "Invert Selection", action: () => handleInvertSelection(activePanel), shortcut: "*" },
      { label: "Copy", action: () => dispatchKey("F5"), shortcut: "F5" },
      { label: "Move / Rename", action: () => dispatchKey("F6"), shortcut: "F6" },
      { label: "Make Directory", action: () => dispatchKey("F7"), shortcut: "F7" },
      { label: "Symbolic Link", action: handleLink },
      { label: "Delete", action: () => dispatchKey("F8"), shortcut: "F8" },
    ],
    "Commands": [
      { label: "NDC tree", action: () => setTreeDlg(true) },
      { label: "Find File", action: () => setSearchDlg({ onResults: handleSearchResults }) },
      { label: "History", action: handleHistory },
      { label: fullscreen ? "  [X] EGA Lines" : "  EGA Lines", action: toggleFullscreen },
      { label: "System Information", action: handleSystemInfo },
      null,
      { label: "Swap panels", action: swapPanels },
      { label: "Panels On/Off", action: () => { setLeftPanelVisible((p) => !p); setRightPanelVisible((p) => !p); } },
      { label: "Compare Directories", action: handleCompare },
      { label: "Synchronize Directories", action: handleSync },
      null,
      { label: "Terminal Emulation", disabled: true },
      null,
      { label: "Menu File Edit", disabled: true },
      { label: "Extension File edit", disabled: true },
      { label: "Editors", disabled: true },
      null,
      { label: "Configuration", action: () => setConfigDlg(true) },
      { label: "Timeouts", action: () => setTimeoutsDlg(true) },
    ],
    "Options": [
      { label: fullscreen ? "  [X] Fullscreen" : "  Fullscreen", action: toggleFullscreen },
      null,
      { label: "Configuration...", action: () => setConfigDlg(true) },
      { label: "Timeouts...", action: () => setTimeoutsDlg(true) },
    ],
    "Right": [
      { label: rightViewMode === "brief" ? "  [X] Brief" : "  Brief", action: () => handleViewMode("brief", "right") },
      { label: rightViewMode === "full" ? "  [X] Full" : "  Full", action: () => handleViewMode("full", "right") },
      { label: rightViewMode === "quick" ? "  [X] Quick view" : "  Quick view", action: () => handleViewMode("quick", "right") },
      { label: rightViewMode === "info" ? "  [X] Info" : "  Info", action: () => handleViewMode("info", "right") },
      { label: rightViewMode === "tree" ? "  [X] Tree" : "  Tree", action: () => handleViewMode("tree", "right") },
      { label: "  Compressed File", action: () => handleCompressedFile("right") },
      { label: rightViewMode === "search" ? "  [X] Find file panel" : "  Find file panel", action: () => { setSearchDlg({ side: "right", onResults: handleSearchResults }); } },
      { label: "  Directory information", action: () => handleDirInfo("right") },
      { label: "  Link", disabled: true },
      { label: rightPanelVisible ? "  [X] On" : "  Off", action: () => setRightPanelVisible((p) => !p) },
      null,
      { label: rightSortBy === "name" ? "  [X] Name" : "  Name", action: () => handleSort("name", "right") },
      { label: rightSortBy === "extension" ? "  [X] Extension" : "  Extension", action: () => handleSort("extension", "right") },
      { label: rightSortBy === "modified" ? "  [X] Time" : "  Time", action: () => handleSort("modified", "right") },
      { label: rightSortBy === "size" ? "  [X] Size" : "  Size", action: () => handleSort("size", "right") },
      { label: rightSortBy === "unsorted" ? "  [X] Unsorted" : "  Unsorted", action: () => handleSort("unsorted", "right") },
      null,
      { label: "Re-read", action: () => fetchDir(rightPath, "right") },
      { label: "Filter...", action: () => setInputDlg({ title: "Filter", label: `Enter file pattern (current: ${rightFilter === "*" ? "all files" : rightFilter}):`, defaultValue: rightFilter, onOk: (val) => { setInputDlg(null); const f = val.trim() || "*"; setRightFilter(f); fetchDir(rightPath, "right", null, null, f); }, onCancel: () => setInputDlg(null) }) },
      { label: "Drive...", action: () => setDriveDlg({ side: "right" }) },
    ],
  };

  const fnButtons = [
    { key: "F1", label: "Help" }, { key: "F2", label: "Menu" }, { key: "F3", label: "View" },
    { key: "F4", label: "Edit" }, { key: "F5", label: "Copy" }, { key: "F6", label: "RenMov" },
    { key: "F7", label: "MkDir" }, { key: "F8", label: "Delete" }, { key: "F9", label: "Search" }, { key: "F10", label: "Quit" },
  ];

  // ═══════════════════════════════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════════════════════════════
  return h("div", { className: "flex-col", style: { width: "100%", maxWidth: 900, margin: "0 auto", fontFamily: MONO, fontSize: config.fontSize, height: "min(88vh, 600px)", background: "#000080", border: "3px solid #0044AA", boxShadow: "0 0 40px rgba(0,0,128,0.4), inset 0 0 80px rgba(0,0,60,0.3)", userSelect: "none", outline: "none", position: "relative" }, tabIndex: 0 },

    // ── Menu bar ────────────────────────────────────────────────────────────
    h("div", { ref: menuRef, className: "flex", style: { justifyContent: "space-between", background: "#000040", padding: "3px 10px", borderBottom: "1px solid #0055AA", color: "#00AAAA", fontSize: 12 } },
      h("div", { className: "flex", style: { gap: 0 } },
        ["Left", "Files", "Commands", "Options", "Right"].map((name) =>
          h("div", { key: name, style: { position: "relative" } },
            h("span", { style: { cursor: "pointer", padding: "1px 8px", background: openMenu === name ? "#00AAAA" : "transparent", color: openMenu === name ? "#000" : "#00AAAA" }, onClick: () => setOpenMenu(openMenu === name ? null : name), onMouseEnter: () => { if (openMenu) setOpenMenu(name); } }, name),
            openMenu === name && h("div", { style: { position: "absolute", top: "100%", left: 0, zIndex: 200, backgroundColor: "#000080", border: "1px solid #00AAAA", minWidth: 180, padding: "2px 0", boxShadow: "2px 2px 0 rgba(0,0,0,0.5)" } },
              menuItems[name].map((item, i) => {
                if (item === null) return h("div", { key: `s${i}`, style: { height: 1, backgroundColor: "#0055AA", margin: "2px 4px" } });
                return h("div", { key: item.label, style: { padding: "2px 8px", cursor: item.disabled ? "default" : "pointer", display: "flex", justifyContent: "space-between", color: item.disabled ? "#555" : "#00FFFF", fontSize: 12, lineHeight: "18px" },
                  onMouseEnter: (e) => { if (!item.disabled) { e.currentTarget.style.backgroundColor = "#00AAAA"; e.currentTarget.style.color = "#000"; } },
                  onMouseLeave: (e) => { if (!item.disabled) { e.currentTarget.style.backgroundColor = "transparent"; e.currentTarget.style.color = "#00FFFF"; } },
                  onClick: () => { if (!item.disabled) { setOpenMenu(null); item.action(); } } },
                  h("span", { style: { whiteSpace: "pre" } }, item.label),
                  item.shortcut ? h("span", { style: { color: "#FFFF00", marginLeft: 12 } }, item.shortcut) : null);
              }))))),
      h("span", { style: { color: "#555599" } }, `WebNC${diskInfo ? ` │ ${fmtSize(diskInfo.free)} free (${diskInfo.percent_used}% used)` : ""}`)),

    // ── Main area (panels overlay terminal) ────────────────────────────────
    h("div", { style: { position: "relative", flex: "1 1 0%", minHeight: 0 } },

      // Terminal (always fills the wrapper, covered by panels when visible)
      h("div", { ref: termRef, className: "flex-col", style: { position: "relative", zIndex: 1, height: "100%", overflowY: "auto", background: "#000", borderTop: activeTarget === "terminal" ? "1px solid #00FFFF" : "1px solid #0055AA", padding: "2px 8px" }, onClick: () => setActiveTarget("terminal") },
        cmdHistory.length === 0 && bothVisible
          ? null
          : cmdHistory.length === 0
            ? h("span", { style: { color: "#333", fontSize: 11, fontStyle: "italic" } }, "Type a command and press Enter")
            : cmdHistory.map((h_, i) =>
                h("div", { key: i, style: { marginBottom: 3 } },
                  h("div", { style: { color: "#FFFF55", fontSize: 11 } }, h_.cmd),
                  h("div", { style: { color: "#AAAAAA", fontSize: 11, whiteSpace: "pre-wrap", wordBreak: "break-all" } }, h_.stdout || `(exit code ${h_.returncode})`)))),

      // Panels (absolutely positioned on top of terminal)
      bothVisible
        ? h("div", { className: "flex gap-4", style: { position: "absolute", inset: 0, zIndex: 10, overflow: "hidden" }, onClick: () => setActiveTarget("panels") },
            leftPanelVisible ? h(Panel, { path: leftPath, items: leftItems, selectedIdx: leftIdx, active: activePanel === "left", selected: leftSelected, loading: leftLoading, error: leftError, viewMode: leftViewMode, preview: leftPreview, infoData: leftInfoData, treeNodes: leftTreeNodes, treeCursor: leftTreeCursor, searchQuery: leftSearchQuery, onTreeToggle: (node) => toggleTreeNode("left", node), onTreeNavigate: (p) => treeNavigateOpposite("left", p), onSelect: (i) => { setLeftIdx(i); setActivePanel("left"); }, onActivate: () => setActivePanel("left"), onNavigate: (item) => navigate(item, "left") }) :
              h("div", { className: "flex-1 flex", style: { alignItems: "center", justifyContent: "center", border: "2px solid #0055AA", background: "#000040", color: "#004488", fontSize: 13 } }, "*** Panel Off ***"),
            rightPanelVisible ? h(Panel, { path: rightPath, items: rightItems, selectedIdx: rightIdx, active: activePanel === "right", selected: rightSelected, loading: rightLoading, error: rightError, viewMode: rightViewMode, preview: rightPreview, infoData: rightInfoData, treeNodes: rightTreeNodes, treeCursor: rightTreeCursor, searchQuery: rightSearchQuery, onTreeToggle: (node) => toggleTreeNode("right", node), onTreeNavigate: (p) => treeNavigateOpposite("right", p), onSelect: (i) => { setRightIdx(i); setActivePanel("right"); }, onActivate: () => setActivePanel("right"), onNavigate: (item) => navigate(item, "right") }) :
              h("div", { className: "flex-1 flex", style: { alignItems: "center", justifyContent: "center", border: "2px solid #0055AA", background: "#000040", color: "#004488", fontSize: 13 } }, "*** Panel Off ***")) : null),

     // ── Command line ────────────────────────────────────────────────────────
    h("div", { className: "flex", style: { alignItems: "center", background: "#000", padding: "3px 8px", borderTop: activeTarget === "terminal" ? "1px solid #00FFFF" : "1px solid #0055AA" } },
      h("span", { style: { color: "#AAAAAA", fontSize: 12 } }, toWinPath(activePanel === "left" ? leftPath : rightPath) + ">"),
      (() => { const f = activePanel === "left" ? leftFilter : rightFilter; return f !== "*" ? h("span", { className: "text-yellow", style: { fontSize: 12, marginLeft: 6 } }, `[${f}]`) : null; })(),
      h("input", { type: "text", value: cmdLine, onChange: (e) => setCmdLine(e.target.value), onClick: () => setActiveTarget("terminal"), onKeyDown: (e) => { if (activeTarget !== "terminal" && keyBindings[e.key]) { e.preventDefault(); return; } if (e.key === "ArrowUp" && cmdHistoryTexts.length > 0) { e.preventDefault(); setCmdHistoryIdx((p) => { const n = Math.min(p + 1, cmdHistoryTexts.length - 1); setCmdLine(cmdHistoryTexts[cmdHistoryTexts.length - 1 - n]); return n; }); return; } if (e.key === "ArrowDown") { e.preventDefault(); setCmdHistoryIdx((p) => { const n = Math.max(p - 1, -1); setCmdLine(n === -1 ? "" : cmdHistoryTexts[cmdHistoryTexts.length - 1 - n]); return n; }); return; } if (e.key === "Enter" && (activeTarget === "terminal" || !bothVisible)) { e.preventDefault(); handleCmdEnter(); } }, style: { background: "transparent", border: "none", color: "#AAAAAA", fontSize: 12, outline: "none", flex: 1, marginLeft: 2, caretColor: "#AAAAAA" }, autoFocus: true })),

    // ── Status bar ──────────────────────────────────────────────────────────
    h("div", { className: "flex", style: { background: connected ? "#000040" : "#440000", color: connected ? "#00AAAA" : "#FF5555", padding: "2px 10px", fontSize: 11, borderTop: "1px solid #0055AA", justifyContent: "space-between" } },
      h("span", null, statusMsg),
      h("span", { style: { color: "#006688", display: "flex", gap: 8 } },
        appVersion ? h("span", { style: { color: "#555599" } }, `v${appVersion}`) : null,
        h("span", { style: { color: activeTarget === "terminal" ? "#00FF00" : "#006688" } }, "Cmd"),
        "↑↓ Enter Ins Tab Alt+F1/F2 F1-F8 · Ctrl+O · Click menu bar")),

    // ── Fn bar ──────────────────────────────────────────────────────────────
    h("div", { className: "flex", style: { background: "#000", borderTop: "1px solid #0055AA" } }, fnButtons.map(({ key, label }) =>
      h("div", { key, className: "flex-1 flex", style: { alignItems: "center", justifyContent: "center", padding: "4px 2px", cursor: "pointer", fontSize: 12, borderRight: "1px solid #333" }, onClick: () => window.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true })), onMouseEnter: (e) => (e.currentTarget.style.background = "#0055AA"), onMouseLeave: (e) => (e.currentTarget.style.background = "transparent") },
        h("span", { className: "text-yellow fw-bold" }, key.replace("F", "")),
        h("span", { style: { color: "#00AAAA", marginLeft: 2 } }, label)))),

    // ── Dialogs ─────────────────────────────────────────────────────────────
    viewer && h(FileViewer, { filename: viewer.filename, content: viewer.content, loading: viewer.loading, type: viewer.type, src: viewer.src, onClose: () => setViewer(null) }),
    editorDlg && h(EditorDialog, { filename: editorDlg.filename, content: editorDlg.content, onSave: (text) => handleEditorSave(editorDlg.path, text), onClose: () => setEditorDlg(null) }),
    dialog && h(ConfirmDialog, { title: dialog.title, message: dialog.message, onYes: dialog.onYes, onNo: dialog.onNo }),
    alertDlg && h(AlertDialog, { message: alertDlg.message, onClose: () => setAlertDlg(null) }),
    inputDlg && h(InputDialog, { title: inputDlg.title, label: inputDlg.label, defaultValue: inputDlg.defaultValue, onOk: inputDlg.onOk, onCancel: inputDlg.onCancel }),
    infoDlg && h(InfoDialog, { info: infoDlg, onClose: () => setInfoDlg(null) }),
    driveDlg && h(DriveDialog, { drives: drivesList, onSelect: (d) => { const np = `/${d.drive[0]}/`; if (driveDlg.side === "left") { setLeftPath(np); fetchDir(np, "left"); } else { setRightPath(np); fetchDir(np, "right"); } setDriveDlg(null); }, onClose: () => setDriveDlg(null) }),
    searchDlg && h(SearchDialog, { onClose: () => setSearchDlg(null), onNavigate: searchNavigate }),
    sysInfoDlg && h(SysInfoDialog, { data: sysInfoDlg, onClose: () => setSysInfoDlg(null) }),
    compareDlg && h(CompareDialog, { data: compareDlg, leftPath, rightPath, onClose: () => setCompareDlg(null), onNavigate: compareNavigate }),
    syncDlg && h(SyncDialog, { plan: syncPlan || [], actions: syncActions, leftPath, rightPath, onCompare: handleSyncCompare, onToggle: syncToggleItem, onSetAll: syncSetAll, onExecute: syncExecute, onClose: () => { setSyncDlg(null); setSyncPlan(null); setSyncActions([]); }, status: syncDlg }),
    historyDlg && h(HistoryDialog, { entries: historyDlg, activePanel, onClose: () => setHistoryDlg(null), onNavigate: (p, side) => { const sp = side === "left" ? setLeftPath : setRightPath; sp(p); fetchDir(p, side); } }),
    configDlg && h(ConfigDialog, { config, onSave: (c) => { saveConfig(c); updateConfig({ showHidden: c.showHidden }); setConfig(c); setConfigDlg(null); refreshBoth(); }, onClose: () => setConfigDlg(null) }),
    timeoutsDlg && h(TimeoutsDialog, { onClose: () => setTimeoutsDlg(null) }),
    treeDlg && h(TreeDialog, { onSelect: (p) => { setLeftPath(p); setRightPath(p); fetchDir(p, "left"); fetchDir(p, "right"); setTreeDlg(null); }, onClose: () => setTreeDlg(null) }),
    helpDlg && h(HelpDialog, { onClose: () => setHelpDlg(null) }),
    archiveDlg && h(ArchiveDialog, { state: archiveDlg, onClose: () => setArchiveDlg(null), onNavigate: () => {} }),
    loginDlg && h(LoginDialog, { error: loginError, onLogin: handleLogin, onClose: () => { if (getToken()) setLoginDlg(null); } }),
    h("style", null, `@keyframes blink { 50% { opacity: 0; } }`));
}
