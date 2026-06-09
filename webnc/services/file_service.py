from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class FileService(ABC):
    """Abstract interface for filesystem operations.

    All methods return plain dicts ready for JSON serialization.
    Platform-specific implementations (Windows, Linux, etc.) subclass this.
    """

    @abstractmethod
    def list_directory(
        self,
        path: str,
        sort_by: str = "name",
        sort_dir: str = "asc",
        show_hidden: bool = False,
        filter: Optional[str] = None,
    ) -> dict:
        ...

    @abstractmethod
    def read_file(self, path: str, encoding: str = "utf-8") -> dict:
        ...

    @abstractmethod
    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> dict:
        ...

    @abstractmethod
    def download_path(self, path: str) -> Path:
        """Return the real filesystem path for download (no size checks)."""
        ...

    @abstractmethod
    def upload(self, dest_dir: str, filename: str, content: bytes) -> dict:
        ...

    @abstractmethod
    def copy(self, src: str, dest: str) -> dict:
        ...

    @abstractmethod
    def move(self, src: str, dest: str) -> dict:
        ...

    @abstractmethod
    def rename(self, path: str, new_name: str) -> dict:
        ...

    @abstractmethod
    def make_directory(self, path: str) -> dict:
        ...

    @abstractmethod
    def create_link(self, target: str, link_path: str) -> dict:
        ...

    @abstractmethod
    def delete(self, path: str, recursive: bool = False) -> dict:
        ...

    @abstractmethod
    def batch_delete(self, paths: list[str], recursive: bool = False) -> dict:
        ...

    @abstractmethod
    def search(self, path: str, pattern: str, max_results: int = 100) -> dict:
        ...

    @abstractmethod
    def file_info(self, path: str) -> dict:
        ...

    @abstractmethod
    def tree(self, path: str) -> dict:
        ...
