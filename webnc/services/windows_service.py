from __future__ import annotations

import ctypes
import ctypes.wintypes
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from webnc.config import MAX_VIEW_SIZE, MAX_UPLOAD_SIZE
from webnc.logging_config import logger
from webnc.models.files import FileInfo
from webnc.services.file_service import FileService
from webnc.vfs.paths import safe_path, relative_path


# ── Windows security helpers ──────────────────────────────────────────────────

def _get_windows_owner(p: Path) -> str:
    try:
        advapi32 = ctypes.windll.advapi32
        path_w = ctypes.create_unicode_buffer(str(p))
        sec_desc_size = ctypes.wintypes.DWORD(0)
        result = advapi32.GetFileSecurityW(path_w, 1, None, 0, ctypes.byref(sec_desc_size))
        if not result and ctypes.GetLastError() != 122:
            return "unknown"
        buf = ctypes.create_string_buffer(sec_desc_size.value)
        result = advapi32.GetFileSecurityW(path_w, 1, buf, sec_desc_size, ctypes.byref(sec_desc_size))
        if not result:
            return "unknown"
        owner_sid = ctypes.c_void_p()
        defaulted = ctypes.wintypes.BOOL()
        result = advapi32.GetSecurityDescriptorOwner(buf, ctypes.byref(owner_sid), ctypes.byref(defaulted))
        if not result or not owner_sid:
            return "unknown"
        name_len, domain_len, snu = ctypes.wintypes.DWORD(0), ctypes.wintypes.DWORD(0), ctypes.wintypes.DWORD()
        advapi32.LookupAccountSidW(None, owner_sid, None, ctypes.byref(name_len), None, ctypes.byref(domain_len), ctypes.byref(snu))
        name_buf = ctypes.create_unicode_buffer(name_len.value)
        domain_buf = ctypes.create_unicode_buffer(domain_len.value)
        result = advapi32.LookupAccountSidW(None, owner_sid, name_buf, ctypes.byref(name_len), domain_buf, ctypes.byref(domain_len), ctypes.byref(snu))
        if result:
            domain = domain_buf.value
            name = name_buf.value
            return f"{domain}\\{name}" if domain else name
        return "unknown"
    except Exception:
        return "unknown"


def _get_windows_permissions(p: Path) -> str:
    try:
        is_dir = p.is_dir()
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(p))
            if attrs == 0xFFFFFFFF:
                raise OSError("GetFileAttributesW failed")
        except Exception:
            return _fallback_perms(p)

        readonly = bool(attrs & 1)
        hidden = bool(attrs & 2)
        prefix = "d" if is_dir else "-"
        owner_r = "r" if not readonly else "-"
        owner_w = "w" if not readonly else "-"
        owner_x = "x" if is_dir else "-"
        other_r = "r" if (not readonly or hidden) else "-"
        return f"{prefix}{owner_r}{owner_w}{owner_x}{owner_r}{owner_w}{owner_x}{other_r}-{other_r}"

    except Exception:
        return _fallback_perms(p)


def _fallback_perms(p: Path) -> str:
    try:
        st = p.stat()
        mode = st.st_mode
        is_dir = p.is_dir()
        perms = "d" if is_dir else "-"
        perms += "r" if (mode & 0o400) else "-"
        perms += "w" if (mode & 0o200) else "-"
        perms += "x" if (mode & 0o100 and is_dir) else "-"
        perms += "r" if (mode & 0o040) else "-"
        perms += "w" if (mode & 0o020) else "-"
        perms += "x" if (mode & 0o010 and is_dir) else "-"
        perms += "r" if (mode & 0o004) else "-"
        perms += "w" if (mode & 0o002) else "-"
        perms += "x" if (mode & 0o001 and is_dir) else "-"
        return perms
    except OSError:
        return "-" * 10


def _build_file_info(p: Path) -> dict:
    try:
        st = p.stat()
        mod_time = datetime.fromtimestamp(st.st_mtime)
        st_size = st.st_size
    except OSError:
        mod_time = datetime.now()
        st_size = 0
        st = None
    return FileInfo(
        name=p.name,
        path=relative_path(p),
        is_dir=p.is_dir(),
        is_symlink=p.is_symlink(),
        size=st_size if st and not p.is_dir() else 0,
        modified=mod_time.isoformat(),
        modified_ts=st.st_mtime if st else 0,
        owner=None,
        permissions=_get_windows_permissions(p),
        extension=p.suffix.lower().lstrip(".") if not p.is_dir() else "",
    ).model_dump()


# ── Windows FileService ───────────────────────────────────────────────────────

class WindowsFileService(FileService):

    def list_directory(
        self,
        path: str,
        sort_by: str = "name",
        sort_dir: str = "asc",
        show_hidden: bool = False,
        filter: Optional[str] = None,
    ) -> dict:
        dir_path = safe_path(path)
        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {path}"}
        if not dir_path.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}

        items = []
        total_size = 0

        try:
            entries = list(dir_path.iterdir())
        except (PermissionError, OSError) as e:
            logger.warning("list: cannot read %s — %s", path, e)
            parent = None
            if not str(dir_path.resolve()).rstrip("\\").endswith(":"):
                parent = relative_path(dir_path.parent)
            return {
                "success": True,
                "path": relative_path(dir_path),
                "parent": parent,
                "items": [],
                "total_files": 0,
                "total_dirs": 0,
                "total_size": 0,
            }

        for entry in entries:
            if not show_hidden and entry.name.startswith("."):
                continue
            if filter and not fnmatch.fnmatch(entry.name, filter):
                continue
            try:
                info = _build_file_info(entry)
                items.append(info)
                total_size += info["size"]
            except OSError:
                continue

        reverse = sort_dir == "desc"
        sort_keys = {
            "name": lambda x: x["name"].lower(),
            "size": lambda x: x["size"],
            "modified": lambda x: x["modified_ts"],
            "extension": lambda x: x["extension"],
        }

        if sort_by == "unsorted":
            dirs = [i for i in items if i["is_dir"]]
            files = [i for i in items if not i["is_dir"]]
            items = dirs + files
        else:
            key_fn = sort_keys.get(sort_by, sort_keys["name"])
            dirs = sorted([i for i in items if i["is_dir"]], key=key_fn, reverse=reverse)
            files = sorted([i for i in items if not i["is_dir"]], key=key_fn, reverse=reverse)
            items = dirs + files

        parent = None
        if not str(dir_path.resolve()).rstrip("\\").endswith(":"):
            parent = relative_path(dir_path.parent)

        return {
            "success": True,
            "path": relative_path(dir_path),
            "parent": parent,
            "items": items,
            "total_files": len(files),
            "total_dirs": len(dirs),
            "total_size": total_size,
        }

    def read_file(self, path: str, encoding: str = "utf-8") -> dict:
        file_path = safe_path(path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        if file_path.is_dir():
            return {"success": False, "error": "Is a directory"}

        st = file_path.stat()
        if st.st_size > MAX_VIEW_SIZE:
            return {"success": False, "error": "File too large to view"}

        try:
            content = file_path.read_text(encoding=encoding, errors="replace")
        except Exception as e:
            logger.exception("read_text failed for %s", path)
            return {"success": False, "error": f"Read error: {e}"}

        import mimetypes
        mime, _ = mimetypes.guess_type(file_path.name)
        return {
            "success": True,
            "path": relative_path(file_path),
            "name": file_path.name,
            "size": st.st_size,
            "mime": mime or "text/plain",
            "content": content,
        }

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> dict:
        file_path = safe_path(path)
        try:
            file_path.write_text(content, encoding=encoding)
        except Exception as e:
            logger.exception("write failed: path=%s", path)
            return {"success": False, "error": str(e)}
        return {"success": True, "path": relative_path(file_path)}

    def download_path(self, path: str) -> Path:
        file_path = safe_path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if file_path.is_dir():
            raise IsADirectoryError("Is a directory")
        return file_path

    def upload(self, dest_dir: str, filename: str, content: bytes) -> dict:
        dir_path = safe_path(dest_dir)
        if not dir_path.is_dir():
            return {"success": False, "error": "Destination is not a directory"}
        dest_file = dir_path / filename
        if len(content) > MAX_UPLOAD_SIZE:
            return {"success": False, "error": "File too large"}
        try:
            dest_file.write_bytes(content)
        except Exception as e:
            logger.exception("upload failed: dest=%s file=%s", dest_dir, filename)
            return {"success": False, "error": str(e)}
        return {"success": True, "path": relative_path(dest_file)}

    def copy(self, src: str, dest: str) -> dict:
        src_path = safe_path(src)
        dest_path = safe_path(dest)
        if not src_path.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        if dest_path.is_dir():
            dest_path = dest_path / src_path.name
        if dest_path.exists():
            return {"success": False, "error": f"Destination already exists: {dest}"}
        try:
            if src_path.is_dir():
                shutil.copytree(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)
        except Exception as e:
            logger.exception("copy failed: src=%s dest=%s", src, dest)
            return {"success": False, "error": str(e)}
        return {"success": True, "path": relative_path(dest_path)}

    def move(self, src: str, dest: str) -> dict:
        src_path = safe_path(src)
        dest_path = safe_path(dest)
        if not src_path.exists():
            return {"success": False, "error": f"Source not found: {src}"}
        if dest_path.is_dir():
            dest_path = dest_path / src_path.name
        if dest_path.exists():
            return {"success": False, "error": f"Destination already exists: {dest}"}
        try:
            shutil.move(str(src_path), str(dest_path))
        except Exception as e:
            logger.exception("move failed: src=%s dest=%s", src, dest)
            return {"success": False, "error": str(e)}
        return {"success": True, "path": relative_path(dest_path)}

    def rename(self, path: str, new_name: str) -> dict:
        src = safe_path(path)
        if not src.exists():
            return {"success": False, "error": f"Not found: {path}"}
        dest = src.parent / new_name
        if dest.exists():
            return {"success": False, "error": f"Name already taken: {new_name}"}
        try:
            src.rename(dest)
        except Exception as e:
            logger.exception("rename failed: path=%s new_name=%s", path, new_name)
            return {"success": False, "error": str(e)}
        return {"success": True, "path": relative_path(dest)}

    def make_directory(self, path: str) -> dict:
        dir_path = safe_path(path)
        if dir_path.exists():
            return {"success": False, "error": f"Already exists: {path}"}
        try:
            dir_path.mkdir(parents=True)
        except Exception as e:
            logger.exception("mkdir failed: path=%s", path)
            return {"success": False, "error": str(e)}
        return {"success": True, "path": relative_path(dir_path)}

    def create_link(self, target: str, link_path: str) -> dict:
        target_path = safe_path(target)
        link = safe_path(link_path)

        if not target_path.exists():
            return {"success": False, "error": f"Target not found: {target}"}
        if link.exists():
            return {"success": False, "error": f"Link already exists: {link_path}"}

        try:
            resolved = target_path.resolve()
        except OSError:
            resolved = target_path.absolute()

        link_parent = link.parent
        cross_drive = resolved.drive != link_parent.drive if resolved.drive and link_parent.drive else False
        created_as = "symlink"

        try:
            if cross_drive:
                raise OSError(1, "cross-drive link, skipping os.symlink")
            os.symlink(str(resolved), str(link))
        except OSError as e:
            win_err = getattr(e, "winerror", None)
            if win_err in (1, 1314) or cross_drive:
                logger.warning("symlink fallback (WinError %s): target=%s link=%s", win_err or "cross-drive", target, link_path)
                try:
                    if target_path.is_dir():
                        cmd = ["cmd", "/c", "mklink", "/J", str(link), str(resolved)]
                    else:
                        cmd = ["cmd", "/c", "mklink", "/H", str(link), str(resolved)]
                    subprocess.check_call(cmd, shell=True)
                    created_as = "junction" if target_path.is_dir() else "hardlink"
                except subprocess.CalledProcessError:
                    logger.warning("mklink failed: target=%s link=%s", target, link_path)
                    hints = []
                    if cross_drive and not target_path.is_dir():
                        hints.append("hard links require same drive")
                    if target_path.is_dir():
                        hints.append("enable Developer Mode in Windows Settings")
                    hint = "; ".join(hints) if hints else "enable Developer Mode or check filesystem permissions"
                    return {"success": False, "error": f"Cannot create link: {hint}"}
            else:
                logger.exception("symlink failed: target=%s link=%s", target, link_path)
                return {"success": False, "error": str(e)}

        return {"success": True, "path": relative_path(link), "created_as": created_as}

    def delete(self, path: str, recursive: bool = False) -> dict:
        target = safe_path(path)
        if not target.exists():
            return {"success": False, "error": f"Not found: {path}"}
        resolved = target.resolve()
        if str(resolved).rstrip("\\").endswith(":"):
            return {"success": False, "error": "Cannot delete drive root"}
        try:
            if target.is_dir():
                if recursive:
                    shutil.rmtree(target)
                else:
                    target.rmdir()
            else:
                target.unlink()
        except OSError as e:
            logger.warning("delete failed: path=%s err=%s", path, e)
            return {"success": False, "error": str(e)}
        return {"success": True}

    def batch_delete(self, paths: list[str], recursive: bool = False) -> dict:
        deleted = []
        errors = []
        for p in paths:
            target = safe_path(p)
            try:
                resolved = target.resolve()
                if str(resolved).rstrip("\\").endswith(":"):
                    errors.append(f"{p}: cannot delete drive root")
                    continue
                if not target.exists():
                    errors.append(f"{p}: not found")
                    continue
                if target.is_dir():
                    if recursive:
                        shutil.rmtree(target)
                    else:
                        target.rmdir()
                else:
                    target.unlink()
                deleted.append(p)
            except Exception as e:
                logger.warning("batch-delete failed: %s err=%s", p, e)
                errors.append(f"{p}: {e}")
        msg = f"Deleted {len(deleted)} item(s)"
        if errors:
            msg += f", {len(errors)} error(s): {'; '.join(errors[:3])}"
        return {"success": len(errors) == 0, "message": msg, "deleted": deleted, "errors": errors}

    def search(self, path: str, pattern: str, max_results: int = 100) -> dict:
        start = safe_path(path)
        if not start.is_dir():
            return {"success": False, "error": "Search path must be a directory"}
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            logger.warning("invalid regex pattern, falling back to glob: %s", pattern)
            escaped = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")
            compiled = re.compile(f"^{escaped}$", re.IGNORECASE)

        results = []
        truncated = False
        for root, dirs, files in os.walk(start):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files + dirs:
                if compiled.search(name):
                    full = Path(root) / name
                    st = full.stat()
                    mod_time = datetime.fromtimestamp(st.st_mtime)
                    results.append(FileInfo(
                        name=full.name,
                        path=relative_path(full),
                        is_dir=full.is_dir(),
                        size=st.st_size if not full.is_dir() else 0,
                        modified=mod_time.isoformat(),
                        modified_ts=st.st_mtime,
                        permissions="-" * 10,
                        extension=full.suffix.lower().lstrip(".") if not full.is_dir() else "",
                    ).model_dump())
                    if len(results) >= max_results:
                        truncated = True
                        break
            if truncated:
                break

        return {"success": True, "results": results, "truncated": truncated}

    def file_info(self, path: str) -> dict:
        target = safe_path(path)
        if not target.exists():
            return {"success": False, "error": f"Not found: {path}"}
        info = _build_file_info(target)
        st = target.stat()
        info["owner"] = _get_windows_owner(target)
        info["permissions"] = _get_windows_permissions(target)
        extra = {
            **info,
            "absolute_path": str(target.resolve()),
            "is_symlink": target.is_symlink(),
            "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
            "accessed": datetime.fromtimestamp(st.st_atime).isoformat(),
        }
        if not target.is_dir() and st.st_size < MAX_VIEW_SIZE:
            try:
                extra["md5"] = hashlib.md5(target.read_bytes()).hexdigest()
            except OSError:
                pass
        if target.is_dir():
            file_count, dir_count, total = 0, 0, 0
            try:
                for entry in target.iterdir():
                    try:
                        if entry.is_file():
                            file_count += 1
                            total += entry.stat().st_size
                        elif entry.is_dir():
                            dir_count += 1
                    except OSError:
                        continue
            except OSError:
                pass
            extra["total_size"] = total
            extra["file_count"] = file_count
            extra["dir_count"] = dir_count
        try:
            du = shutil.disk_usage(target.anchor if str(target.anchor) != "" else "C:\\")
            extra["disk_total"] = du.total
            extra["disk_free"] = du.free
            extra["disk_used"] = du.used
            extra["disk_percent_used"] = round(du.used / du.total * 100, 1)
        except Exception:
            pass
        return {"success": True, "data": extra}

    def tree(self, path: str) -> dict:
        target = safe_path(path)
        if not target.exists():
            return {"success": False, "error": f"Not found: {path}"}
        if not target.is_dir():
            return {"success": True, "path": path, "name": target.name, "dirs": []}
        entries = []
        try:
            for e in target.iterdir():
                if e.is_dir():
                    entries.append({"name": e.name, "path": relative_path(e)})
        except OSError:
            logger.warning("tree: iterdir failed for %s", path)
        entries.sort(key=lambda d: d["name"].lower())
        return {"success": True, "path": path, "name": target.name or str(target), "dirs": entries}
