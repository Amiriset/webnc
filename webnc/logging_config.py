import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_log_dir = Path(__file__).resolve().parent.parent / "logs"

logger = logging.getLogger("webnc_server")
logger.setLevel(logging.INFO)
_fmt = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if not logger.handlers:
    _sh = logging.StreamHandler()
    _sh.setFormatter(_fmt)
    logger.addHandler(_sh)

    _fh = RotatingFileHandler(
        _log_dir / "webnc_server.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    _fh.setFormatter(_fmt)
    logger.addHandler(_fh)
