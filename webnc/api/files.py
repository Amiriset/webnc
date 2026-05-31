import asyncio
import mimetypes
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse

from webnc.config import MAX_UPLOAD_SIZE
from webnc.logging_config import logger
from webnc.models.files import (
    DirListing,
    OperationResult,
    CopyMoveRequest,
    RenameRequest,
    MkdirRequest,
    DeleteRequest,
    BatchDeleteRequest,
    SearchRequest,
    EditRequest,
)
from webnc.operations.files import (
    ListOperation,
    ViewOperation,
    WriteOperation,
    DownloadOperation,
    UploadOperation,
    CopyOperation,
    MoveOperation,
    RenameOperation,
    MakeDirectoryOperation,
    DeleteOperation,
    BatchDeleteOperation,
    SearchOperation,
    FileInfoOperation,
    TreeOperation,
)
from webnc.operations.queue import OperationQueue

router = APIRouter()

FS_TIMEOUT = 10.0


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


def _get_cm():
    from webnc.main import config_manager
    return config_manager


def _check_edit_size(virtual_path: str) -> None:
    from webnc.vfs.paths import safe_path
    cm = _get_cm()
    max_size = cm.get_max_edit_size()
    if max_size <= 0:
        return
    try:
        real = safe_path(virtual_path)
        size = os.path.getsize(real)
        if size > max_size:
            logger.warning("File too large for editor: %s (%d > %d)", virtual_path, size, max_size)
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({size} bytes). Max edit size: {max_size} bytes ({max_size // 1024} KB). Use F3 (View) for read-only.",
            )
    except OSError:
        pass
    from webnc.main import operation_queue
    return operation_queue


# ──── Directory listing ──────────────────────────────────────────────────────

@router.get("/api/list", response_model=DirListing)
async def list_directory(
    path: str = Query("/", description="Directory path to list"),
    sort_by: str = Query("name", description="Sort field: name, size, modified, extension"),
    sort_dir: str = Query("asc", description="Sort direction: asc or desc"),
    show_hidden: bool = Query(False, description="Show hidden files (dotfiles)"),
    filter: Optional[str] = Query(None, description="Wildcard filter pattern (e.g. *.txt)"),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("GET /api/list  path=%s sort=%s %s filter=%s", path, sort_by, sort_dir, filter or "*")
    op = ListOperation(path=path, sort_by=sort_by, sort_dir=sort_dir, show_hidden=show_hidden, filter=filter)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return DirListing(**data)


# ──── File viewing / content ─────────────────────────────────────────────────

@router.get("/api/view")
async def view_file(
    path: str = Query(..., description="File path to view"),
    encoding: str = Query("utf-8", description="Text encoding"),
    queue: OperationQueue = Depends(get_queue),
    for_edit: bool = Query(False, description="If true, check max_edit_size limit"),
):
    logger.info("GET /api/view  path=%s encoding=%s for_edit=%s", path, encoding, for_edit)
    if for_edit:
        _check_edit_size(path)
    op = ViewOperation(path=path, encoding=encoding)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return data


# ──── File edit / save ───────────────────────────────────────────────────────

@router.post("/api/edit", response_model=OperationResult)
async def edit_file(
    req: EditRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/edit  path=%s content_len=%d", req.path, len(req.content))
    op = WriteOperation(path=req.path, content=req.content)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return OperationResult(success=True, message=f"Saved {req.path}", path=data["path"])


# ──── File download ──────────────────────────────────────────────────────────

@router.get("/api/download")
async def download_file(
    path: str = Query(...),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("GET /api/download  path=%s", path)
    op = DownloadOperation(path=path)
    await queue.run_sync(op, timeout=FS_TIMEOUT)
    file_path = op._path
    return FileResponse(
        file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


# ──── File upload ────────────────────────────────────────────────────────────

@router.post("/api/upload", response_model=OperationResult)
async def upload_file(
    dest_dir: str = Query("/", description="Destination directory"),
    file: UploadFile = File(...),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/upload  dest=%s file=%s size=%s", dest_dir, file.filename, file.size)
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    op = UploadOperation(dest_dir=dest_dir, filename=file.filename, content=content)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return OperationResult(success=True, message=f"Uploaded {file.filename}", path=data["path"])


# ──── Copy (F5) ──────────────────────────────────────────────────────────────

@router.post("/api/copy")
async def copy_item(
    req: CopyMoveRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/copy  src=%s dest=%s", req.src, req.dest)
    op = CopyOperation(src=req.src, dest=req.dest)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}


# ──── Move / Rename (F6) ─────────────────────────────────────────────────────

@router.post("/api/move")
async def move_item(
    req: CopyMoveRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/move  src=%s dest=%s", req.src, req.dest)
    op = MoveOperation(src=req.src, dest=req.dest)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}


# ──── Rename ─────────────────────────────────────────────────────────────────

@router.post("/api/rename", response_model=OperationResult)
async def rename_item(
    req: RenameRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/rename  path=%s new_name=%s", req.path, req.new_name)
    op = RenameOperation(path=req.path, new_name=req.new_name)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return OperationResult(success=True, message=f"Renamed \u2192 {req.new_name}", path=data["path"])


# ──── Create directory (F7) ──────────────────────────────────────────────────

@router.post("/api/mkdir", response_model=OperationResult)
async def make_directory(
    req: MkdirRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/mkdir  path=%s", req.path)
    op = MakeDirectoryOperation(path=req.path)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return OperationResult(success=True, message=f"Created {data['path']}", path=data["path"])


# ──── Delete (F8) ────────────────────────────────────────────────────────────

@router.post("/api/delete", response_model=OperationResult)
async def delete_item(
    req: DeleteRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/delete  path=%s recursive=%s", req.path, req.recursive)
    op = DeleteOperation(path=req.path, recursive=req.recursive)
    await queue.run_sync(op, timeout=FS_TIMEOUT)
    return OperationResult(success=True, message=f"Deleted {req.path}")


# ──── Batch delete ───────────────────────────────────────────────────────────

@router.post("/api/batch-delete")
async def batch_delete(
    req: BatchDeleteRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/batch-delete  paths=%d items recursive=%s", len(req.paths), req.recursive)
    op = BatchDeleteOperation(paths=req.paths, recursive=req.recursive)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}


# ──── Search (Alt+F7) ────────────────────────────────────────────────────────

@router.post("/api/search")
async def search_files(
    req: SearchRequest,
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("POST /api/search  path=%s pattern=%s max=%d", req.path, req.pattern, req.max_results)
    op = SearchOperation(path=req.path, pattern=req.pattern, max_results=req.max_results)
    op_id = queue.add_operation(op)
    return {"operation_id": op_id, "status": "QUEUED", "poll": op.get_poll_config()}


# ──── File info / stat ───────────────────────────────────────────────────────

@router.get("/api/info")
async def file_info(
    path: str = Query(...),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("GET /api/info  path=%s", path)
    op = FileInfoOperation(path=path)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return data


# ──── Directory Tree ─────────────────────────────────────────────────────────

@router.get("/api/tree")
async def tree(
    path: str = Query(...),
    queue: OperationQueue = Depends(get_queue),
):
    logger.info("GET /api/tree  path=%s", path)
    op = TreeOperation(path=path)
    data = await queue.run_sync(op, timeout=FS_TIMEOUT)
    return data
