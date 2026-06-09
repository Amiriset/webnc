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
    LinkRequest,
)
from webnc.operations.files import (
    CopyOperation,
    MoveOperation,
    BatchDeleteOperation,
    SearchOperation,
)
from webnc.operations.queue import OperationQueue
from webnc.services.file_service import FileService

router = APIRouter()

FS_TIMEOUT = 10.0


def get_queue() -> OperationQueue:
    from webnc.main import operation_queue
    return operation_queue


def get_file_service() -> FileService:
    from webnc.main import file_service
    return file_service


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


# ──── Directory listing ──────────────────────────────────────────────────────

@router.get("/api/list", response_model=DirListing)
async def list_directory(
    path: str = Query("/", description="Directory path to list"),
    sort_by: str = Query("name", description="Sort field: name, size, modified, extension"),
    sort_dir: str = Query("asc", description="Sort direction: asc or desc"),
    show_hidden: bool = Query(False, description="Show hidden files (dotfiles)"),
    filter: Optional[str] = Query(None, description="Wildcard filter pattern (e.g. *.txt)"),
    fs: FileService = Depends(get_file_service),
):
    logger.info("GET /api/list  path=%s sort=%s %s filter=%s", path, sort_by, sort_dir, filter or "*")
    result = fs.list_directory(path, sort_by, sort_dir, show_hidden, filter)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return DirListing(**result)


# ──── File viewing / content ─────────────────────────────────────────────────

@router.get("/api/view")
async def view_file(
    path: str = Query(..., description="File path to view"),
    encoding: str = Query("utf-8", description="Text encoding"),
    fs: FileService = Depends(get_file_service),
    for_edit: bool = Query(False, description="If true, check max_edit_size limit"),
):
    logger.info("GET /api/view  path=%s encoding=%s for_edit=%s", path, encoding, for_edit)
    if for_edit:
        _check_edit_size(path)
    result = fs.read_file(path, encoding)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result


# ──── File edit / save ───────────────────────────────────────────────────────

@router.post("/api/edit", response_model=OperationResult)
async def edit_file(
    req: EditRequest,
    fs: FileService = Depends(get_file_service),
):
    logger.info("POST /api/edit  path=%s content_len=%d", req.path, len(req.content))
    result = fs.write_file(req.path, req.content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return OperationResult(success=True, message=f"Saved {req.path}", path=result["path"])


# ──── File download ──────────────────────────────────────────────────────────

@router.get("/api/download")
async def download_file(
    path: str = Query(...),
    fs: FileService = Depends(get_file_service),
):
    logger.info("GET /api/download  path=%s", path)
    try:
        file_path = fs.download_path(path)
    except (FileNotFoundError, IsADirectoryError) as e:
        raise HTTPException(status_code=400, detail=str(e))
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
    fs: FileService = Depends(get_file_service),
):
    logger.info("POST /api/upload  dest=%s file=%s size=%s", dest_dir, file.filename, file.size)
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    result = fs.upload(dest_dir, file.filename, content)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return OperationResult(success=True, message=f"Uploaded {file.filename}", path=result["path"])


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
    fs: FileService = Depends(get_file_service),
):
    logger.info("POST /api/rename  path=%s new_name=%s", req.path, req.new_name)
    result = fs.rename(req.path, req.new_name)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return OperationResult(success=True, message=f"Renamed \u2192 {req.new_name}", path=result["path"])


# ──── Create directory (F7) ──────────────────────────────────────────────────

@router.post("/api/mkdir", response_model=OperationResult)
async def make_directory(
    req: MkdirRequest,
    fs: FileService = Depends(get_file_service),
):
    logger.info("POST /api/mkdir  path=%s", req.path)
    result = fs.make_directory(req.path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return OperationResult(success=True, message=f"Created {result['path']}", path=result["path"])


# ──── Symbolic link ──────────────────────────────────────────────────────────

@router.post("/api/link", response_model=OperationResult)
async def create_link(
    req: LinkRequest,
    fs: FileService = Depends(get_file_service),
):
    logger.info("POST /api/link  target=%s link_path=%s", req.target, req.link_path)
    result = fs.create_link(req.target, req.link_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    kind = result.get("created_as", "symlink")
    label = {"symlink": "SymLinked", "junction": "Junction", "hardlink": "HardLinked", "mklink": "Linked"}.get(kind, "Linked")
    return OperationResult(success=True, message=f"{label} \u2192 {result['path']}", path=result["path"])


# ──── Delete (F8) ────────────────────────────────────────────────────────────

@router.post("/api/delete", response_model=OperationResult)
async def delete_item(
    req: DeleteRequest,
    fs: FileService = Depends(get_file_service),
):
    logger.info("POST /api/delete  path=%s recursive=%s", req.path, req.recursive)
    result = fs.delete(req.path, req.recursive)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
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
    fs: FileService = Depends(get_file_service),
):
    logger.info("GET /api/info  path=%s", path)
    result = fs.file_info(path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result.get("data", result)


# ──── Directory Tree ─────────────────────────────────────────────────────────

@router.get("/api/tree")
async def tree(
    path: str = Query(...),
    fs: FileService = Depends(get_file_service),
):
    logger.info("GET /api/tree  path=%s", path)
    result = fs.tree(path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    return result
