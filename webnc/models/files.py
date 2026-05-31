from typing import Optional

from pydantic import BaseModel, field_validator


class FileInfo(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified: str
    modified_ts: float
    permissions: str
    extension: str


class DirListing(BaseModel):
    path: str
    parent: Optional[str]
    items: list[FileInfo]
    total_files: int
    total_dirs: int
    total_size: int


class OperationResult(BaseModel):
    success: bool
    message: str
    path: Optional[str] = None


class CopyMoveRequest(BaseModel):
    src: str
    dest: str

    @field_validator("src", "dest")
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("path must not be empty")
        return v


class RenameRequest(BaseModel):
    path: str
    new_name: str

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip() or "/" in v or "\\" in v:
            raise ValueError("invalid filename")
        return v.strip()


class MkdirRequest(BaseModel):
    path: str


class DeleteRequest(BaseModel):
    path: str
    recursive: bool = False


class BatchDeleteRequest(BaseModel):
    paths: list[str]
    recursive: bool = False


class SearchRequest(BaseModel):
    path: str = "/"
    pattern: str
    max_results: int = 100


class EditRequest(BaseModel):
    path: str
    content: str
