import os
import string
from pathlib import Path


DRIVE_LETTERS = set(string.ascii_uppercase)


def safe_path(user_path: str) -> Path:
    """Convert URL path like /C/Users/foo to Windows absolute path (no FS access)."""
    cleaned = user_path.strip().replace("\\", "/").strip("/")
    if not cleaned:
        return Path("C:\\")
    parts = cleaned.split("/", 1)
    if len(parts[0]) == 1 and parts[0].upper() in DRIVE_LETTERS:
        drive = parts[0].upper() + ":\\"
        rest = parts[1].replace("/", "\\") if len(parts) > 1 else ""
        return Path(os.path.normpath(drive + rest))
    return Path(os.path.normpath("C:\\" + cleaned.replace("/", "\\")))


def relative_path(absolute: Path) -> str:
    """Convert Windows absolute path to URL path like /C/Users/foo (no FS access)."""
    abs_str = str(absolute)
    drive = abs_str[0].upper()
    rest = abs_str[3:].replace("\\", "/")
    if rest:
        return f"/{drive}/{rest}"
    return f"/{drive}/"
