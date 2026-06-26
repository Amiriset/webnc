from __future__ import annotations

import fnmatch
import hashlib
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from webnc.config import MAX_VIEW_SIZE, MAX_UPLOAD_SIZE
from webnc.logging_config import logger
from webnc.models.files import FileInfo
from webnc.operations.base import AbstractOperation, OperationResult, OperationStatus
from webnc.vfs.paths import safe_path, relative_path


class CopyOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "copy"

    def __init__(self, src: str, dest: str, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        return True

    def execute(self) -> OperationResult[dict]:
        src = safe_path(self.src)
        dest = safe_path(self.dest)

        if not src.exists():
            return OperationResult(success=False, error_message=f"Source not found: {self.src}")

        if dest.is_dir():
            dest = dest / src.name

        if dest.exists():
            return OperationResult(success=False, error_message=f"Destination already exists: {self.dest}")

        try:
            if src.is_dir():
                shutil.copytree(src, dest)
            else:
                shutil.copy2(src, dest)
        except Exception as e:
            logger.exception("copy failed: src=%s dest=%s", self.src, self.dest)
            return OperationResult(success=False, error_message=str(e))

        self.set_progress(1.0, "Done")
        return OperationResult(success=True, data={"path": relative_path(dest)})


class MoveOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "move"

    def __init__(self, src: str, dest: str, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        return True

    def execute(self) -> OperationResult[dict]:
        src = safe_path(self.src)
        dest = safe_path(self.dest)

        if not src.exists():
            return OperationResult(success=False, error_message=f"Source not found: {self.src}")

        if dest.is_dir():
            dest = dest / src.name

        if dest.exists():
            return OperationResult(success=False, error_message=f"Destination already exists: {self.dest}")

        try:
            shutil.move(str(src), str(dest))
        except Exception as e:
            logger.exception("move failed: src=%s dest=%s", self.src, self.dest)
            return OperationResult(success=False, error_message=str(e))

        return OperationResult(success=True, data={"path": relative_path(dest)})


class RenameOperation(AbstractOperation[dict]):
    def __init__(self, path: str, new_name: str, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.new_name = new_name

    def execute(self) -> OperationResult[dict]:
        src = safe_path(self.path)
        if not src.exists():
            return OperationResult(success=False, error_message=f"Not found: {self.path}")

        dest = src.parent / self.new_name
        if dest.exists():
            return OperationResult(success=False, error_message=f"Name already taken: {self.new_name}")

        try:
            src.rename(dest)
        except Exception as e:
            logger.exception("rename failed: path=%s new_name=%s", self.path, self.new_name)
            return OperationResult(success=False, error_message=str(e))

        return OperationResult(success=True, data={"path": relative_path(dest)})


class MakeDirectoryOperation(AbstractOperation[dict]):
    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        self.path = path

    def execute(self) -> OperationResult[dict]:
        dir_path = safe_path(self.path)
        if dir_path.exists():
            return OperationResult(success=False, error_message=f"Already exists: {self.path}")

        try:
            dir_path.mkdir(parents=True)
        except Exception as e:
            logger.exception("mkdir failed: path=%s", self.path)
            return OperationResult(success=False, error_message=str(e))

        return OperationResult(success=True, data={"path": relative_path(dir_path)})


class DeleteOperation(AbstractOperation[dict]):
    def __init__(self, path: str, recursive: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.recursive = recursive

    def execute(self) -> OperationResult[dict]:
        target = safe_path(self.path)
        if not target.exists():
            return OperationResult(success=False, error_message=f"Not found: {self.path}")

        resolved = target.resolve()
        if str(resolved).rstrip("\\").endswith(":"):
            return OperationResult(success=False, error_message="Cannot delete drive root")

        try:
            if target.is_dir():
                if self.recursive:
                    shutil.rmtree(target)
                else:
                    target.rmdir()
            else:
                target.unlink()
        except OSError as e:
            logger.warning("delete failed: path=%s err=%s", self.path, e)
            return OperationResult(success=False, error_message=str(e))

        return OperationResult(success=True)


class BatchDeleteOperation(AbstractOperation[dict]):
    should_run_in_queue = True
    op_config_key = "batch_delete"

    def __init__(self, paths: list[str], recursive: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.paths = paths
        self.recursive = recursive

    def should_retry(self, exception: Exception) -> bool:
        if self._is_non_retriable(exception):
            return False
        return True

    def execute(self) -> OperationResult[dict]:
        deleted = []
        errors = []
        total = len(self.paths)

        for i, p in enumerate(self.paths):
            if self.cancel_requested:
                break
            self.set_progress(i / total, f"Deleting {p}")

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
                    if self.recursive:
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

        return OperationResult(success=len(errors) == 0, data={"message": msg, "deleted": deleted, "errors": errors})


class SearchOperation(AbstractOperation[list]):
    should_run_in_queue = True
    op_config_key = "search"

    def __init__(self, path: str, pattern: str, max_results: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.pattern = pattern
        self.max_results = max_results

    def execute(self) -> OperationResult[list]:
        start = safe_path(self.path)
        if not start.is_dir():
            return OperationResult(success=False, error_message="Search path must be a directory")

        try:
            compiled = re.compile(self.pattern, re.IGNORECASE)
        except re.error:
            logger.warning("invalid regex pattern, falling back to glob: %s", self.pattern)
            escaped = re.escape(self.pattern).replace(r"\*", ".*").replace(r"\?", ".")
            compiled = re.compile(f"^{escaped}$", re.IGNORECASE)

        results = []
        truncated = False
        for root, dirs, files in os.walk(start):
            if self.cancel_requested:
                break
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for name in files + dirs:
                if self.cancel_requested:
                    truncated = True
                    break
                if compiled.search(name):
                    full = Path(root) / name
                    st = full.stat()
                    mod_time = datetime.fromtimestamp(st.st_mtime)
                    perms = "-" * 10
                    results.append(FileInfo(
                        name=full.name,
                        path=relative_path(full),
                        is_dir=full.is_dir(),
                        size=st.st_size if not full.is_dir() else 0,
                        modified=mod_time.isoformat(),
                        modified_ts=st.st_mtime,
                        permissions=perms,
                        extension=full.suffix.lower().lstrip(".") if not full.is_dir() else "",
                    ).model_dump())
                    if len(results) >= self.max_results:
                        truncated = True
                        break
            if truncated:
                break

        return OperationResult(success=True, data={"results": results, "truncated": truncated})


def _build_file_info(p: Path) -> dict:
    try:
        st = p.stat()
        mod_time = datetime.fromtimestamp(st.st_mtime)
        perms = "-" * 10
        st_size = st.st_size
    except OSError:
        mod_time = datetime.now()
        perms = "-" * 10
        st_size = 0
        st = None

    return FileInfo(
        name=p.name,
        path=relative_path(p),
        is_dir=p.is_dir(),
        size=st_size if st and not p.is_dir() else 0,
        modified=mod_time.isoformat(),
        modified_ts=st.st_mtime if st else 0,
        permissions=perms,
        extension=p.suffix.lower().lstrip(".") if not p.is_dir() else "",
    ).model_dump()


class ListOperation(AbstractOperation[dict]):
    def __init__(self, path: str, sort_by: str = "name", sort_dir: str = "asc",
                 show_hidden: bool = False, filter: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.sort_by = sort_by
        self.sort_dir = sort_dir
        self.show_hidden = show_hidden
        self.filter = filter

    def execute(self) -> OperationResult[dict]:
        dir_path = safe_path(self.path)
        if not dir_path.exists():
            return OperationResult(success=False, error_message=f"Directory not found: {self.path}")
        if not dir_path.is_dir():
            return OperationResult(success=False, error_message=f"Not a directory: {self.path}")

        items = []
        total_size = 0
        show_hidden = self.show_hidden
        filter = self.filter

        for entry in dir_path.iterdir():
            if not show_hidden and entry.name.startswith("."):
                continue
            if filter and not fnmatch.fnmatch(entry.name, filter):
                continue
            try:
                info = _build_file_info(entry)
                items.append(info)
                total_size += info["size"]
            except OSError:
                logger.warning("skip unreadable entry %s", entry)
                continue

        reverse = self.sort_dir == "desc"
        sort_keys = {
            "name": lambda x: x["name"].lower(),
            "size": lambda x: x["size"],
            "modified": lambda x: x["modified_ts"],
            "extension": lambda x: x["extension"],
        }

        if self.sort_by == "unsorted":
            dirs = [i for i in items if i["is_dir"]]
            files = [i for i in items if not i["is_dir"]]
            items = dirs + files
        else:
            key_fn = sort_keys.get(self.sort_by, sort_keys["name"])
            dirs = sorted([i for i in items if i["is_dir"]], key=key_fn, reverse=reverse)
            files = sorted([i for i in items if not i["is_dir"]], key=key_fn, reverse=reverse)
            items = dirs + files

        parent = None
        if not str(dir_path.resolve()).rstrip("\\").endswith(":"):
            parent = relative_path(dir_path.parent)

        return OperationResult(success=True, data={
            "path": relative_path(dir_path),
            "parent": parent,
            "items": items,
            "total_files": len(files),
            "total_dirs": len(dirs),
            "total_size": total_size,
        })


class ViewOperation(AbstractOperation[dict]):
    def __init__(self, path: str, encoding: str = "utf-8", **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.encoding = encoding

    def execute(self) -> OperationResult[dict]:
        file_path = safe_path(self.path)
        if not file_path.exists():
            return OperationResult(success=False, error_message=f"File not found: {self.path}")
        if file_path.is_dir():
            return OperationResult(success=False, error_message="Is a directory")

        st = file_path.stat()
        if st.st_size > MAX_VIEW_SIZE:
            return OperationResult(success=False, error_message="File too large to view")

        try:
            content = file_path.read_text(encoding=self.encoding, errors="replace")
        except Exception as e:
            logger.exception("read_text failed for %s", self.path)
            return OperationResult(success=False, error_message=f"Read error: {e}")

        mime = None
        import mimetypes
        mime, _ = mimetypes.guess_type(file_path.name)
        return OperationResult(success=True, data={
            "path": relative_path(file_path),
            "name": file_path.name,
            "size": st.st_size,
            "mime": mime or "text/plain",
            "content": content,
        })


class WriteOperation(AbstractOperation[dict]):
    """Write text content to a file (inline editor save)."""

    def __init__(self, path: str, content: str, encoding: str = "utf-8", **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self.content = content
        self.encoding = encoding

    def execute(self) -> OperationResult[dict]:
        file_path = safe_path(self.path)
        try:
            file_path.write_text(self.content, encoding=self.encoding)
        except Exception as e:
            logger.exception("write failed: path=%s", self.path)
            return OperationResult(success=False, error_message=str(e))
        return OperationResult(success=True, data={"path": relative_path(file_path)})


class DownloadOperation(AbstractOperation[dict]):
    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        self.path = path
        self._path = None

    def execute(self) -> OperationResult[dict]:
        file_path = safe_path(self.path)
        if not file_path.exists():
            return OperationResult(success=False, error_message=f"File not found: {self.path}")
        if file_path.is_dir():
            return OperationResult(success=False, error_message="Is a directory")
        self._path = file_path
        return OperationResult(success=True, data={"path": str(file_path)})


class UploadOperation(AbstractOperation[dict]):
    def __init__(self, dest_dir: str, filename: str, content: bytes, **kwargs):
        super().__init__(**kwargs)
        self.dest_dir = dest_dir
        self.filename = filename
        self.content = content

    def execute(self) -> OperationResult[dict]:
        dir_path = safe_path(self.dest_dir)
        if not dir_path.is_dir():
            return OperationResult(success=False, error_message="Destination is not a directory")

        dest_file = dir_path / self.filename
        if len(self.content) > MAX_UPLOAD_SIZE:
            return OperationResult(success=False, error_message="File too large")

        try:
            dest_file.write_bytes(self.content)
        except Exception as e:
            logger.exception("upload failed: dest=%s file=%s", self.dest_dir, self.filename)
            return OperationResult(success=False, error_message=str(e))

        return OperationResult(success=True, data={"path": relative_path(dest_file)})


class FileInfoOperation(AbstractOperation[dict]):
    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        self.path = path

    def execute(self) -> OperationResult[dict]:
        target = safe_path(self.path)
        if not target.exists():
            return OperationResult(success=False, error_message=f"Not found: {self.path}")

        info = _build_file_info(target)
        st = target.stat()

        extra = {
            **info,
            "absolute_path": str(target.resolve()),
            "is_symlink": target.is_symlink(),
            "owner": "unknown",
            "created": datetime.fromtimestamp(st.st_ctime).isoformat(),
            "accessed": datetime.fromtimestamp(st.st_atime).isoformat(),
        }

        if not target.is_dir() and st.st_size < MAX_VIEW_SIZE:
            try:
                extra["md5"] = hashlib.md5(target.read_bytes()).hexdigest()
            except OSError:
                pass

        if target.is_dir():
            file_count = 0
            dir_count = 0
            total = 0
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

        return OperationResult(success=True, data=extra)


class TreeOperation(AbstractOperation[dict]):
    def __init__(self, path: str, **kwargs):
        super().__init__(**kwargs)
        self.path = path

    def execute(self) -> OperationResult[dict]:
        target = safe_path(self.path)
        if not target.exists():
            return OperationResult(success=False, error_message=f"Not found: {self.path}")

        if not target.is_dir():
            return OperationResult(success=True, data={"path": self.path, "name": target.name, "dirs": []})

        entries = []
        try:
            for e in target.iterdir():
                if e.is_dir():
                    entries.append({"name": e.name, "path": relative_path(e)})
        except OSError:
            logger.warning("tree: iterdir failed for %s", self.path)

        entries.sort(key=lambda d: d["name"].lower())
        return OperationResult(success=True, data={
            "path": self.path,
            "name": target.name or str(target),
            "dirs": entries,
        })
