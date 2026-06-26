from pathlib import Path


_project_root = Path(__file__).resolve().parent.parent
_version_file = _project_root / "version.txt"

try:
    VERSION = _version_file.read_text(encoding="utf-8").strip()
except (FileNotFoundError, OSError):
    VERSION = "0.0.0"
