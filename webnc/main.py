"""
WebNC — Application Entry Point
================================
Wires together FastAPI app, middleware, routers, auth, and CLI.
"""

import sys
import warnings
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Suppress noisy asyncio proactor warnings on Windows client disconnect
warnings.filterwarnings("ignore", message=".*_ProactorBasePipeTransport.*")

# Ensure the project root is on sys.path so that `webnc` is importable
# when running `python webnc_server.py` or `python webnc/main.py`.
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from webnc.logging_config import logger
from webnc.models.state import ServerState
from webnc.security import (
    set_auth_provider,
    ConsoleTokenProvider,
    SessionAuthMiddleware,
)
from webnc.api.files import router as files_router
from webnc.api.drives import router as drives_router
from webnc.api.system import router as system_router
from webnc.api.compare import router as compare_router
from webnc.api.sync import router as sync_router
from webnc.api.archive import router as archive_router
from webnc.api.static import router as static_router
from webnc.api.operations import router as operations_router
from webnc.api.config_api import router as config_router
from webnc.api.exec import router as exec_router
from webnc.config_manager import ConfigManager
from webnc.operations.queue import OperationQueue

# ── Globals ────────────────────────────────────────────────────────────────
operation_queue = OperationQueue(max_workers=4)
config_manager = ConfigManager()


def create_app():
    """Build and configure the FastAPI application (no auth provider set)."""
    app = FastAPI(
        title="WebNC API",
        version="1.0.0",
        description="File system operations API for WebNC file manager",
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Session auth middleware ───────────────────────────────────────────
    app.add_middleware(SessionAuthMiddleware)

    # ── Module registry ───────────────────────────────────────────────────
    app.state.modules: dict = {}

    # ── Server state machine ──────────────────────────────────────────────
    app.state.server_state = ServerState.STARTING

    @app.on_event("startup")
    async def _on_startup():
        app.state.server_state = ServerState.RUNNING
        logger.info("Server state: running")
        if hasattr(app.state, "operation_queue"):
            logger.info("Initialized operation queue")

    @app.on_event("shutdown")
    async def _on_shutdown():
        logger.info("Shutting down operation queue...")
        operation_queue.shutdown(wait=True)

    # ── Mount routers ─────────────────────────────────────────────────────
    app.include_router(files_router)
    app.include_router(drives_router)
    app.include_router(system_router)
    app.include_router(compare_router)
    app.include_router(sync_router)
    app.include_router(archive_router)
    app.include_router(static_router)
    app.include_router(operations_router)
    app.include_router(config_router)
    app.include_router(exec_router)

    return app


# ── Global app instance (used by uvicorn) ────────────────────────────────────
app = create_app()
# NOTE: Auth provider is NOT set at module level — it's initialized inside main().
# For `uvicorn webnc.main:app`, requests will get 401 until a provider is set.
# Deployment always goes through main() via `python webnc_server.py` or `python -m webnc`.


# ── CLI entry point ──────────────────────────────────────────────────────────

def main():
    import argparse
    import ssl

    parser = argparse.ArgumentParser(
        description="WebNC API Server"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind port (default: 8000)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL/TLS (HTTP, no encryption)",
    )
    parser.add_argument(
        "--cert", default=None, help="Path to SSL certificate file"
    )
    parser.add_argument(
        "--key", default=None, help="Path to SSL key file"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (default: off)",
    )
    parser.add_argument(
        "--auth",
        default="console-token",
        choices=["console-token"],
        help="Auth provider (default: console-token)",
    )
    args = parser.parse_args()

    # Override auth provider from CLI arg (reuses the global app)
    if args.auth == "console-token":
        set_auth_provider(ConsoleTokenProvider())

    ssl_kw = {}
    if not args.insecure:
        if args.cert and args.key:
            ssl_kw["ssl_certfile"] = args.cert
            ssl_kw["ssl_keyfile"] = args.key
        else:
            app.state.server_state = ServerState.GENERATING_CERT
            from webnc.security.tls import gen_self_signed_cert

            cert_dir = Path(__file__).resolve().parent.parent
            cert_path, key_path = gen_self_signed_cert(cert_dir)
            ssl_kw["ssl_certfile"] = str(cert_path)
            ssl_kw["ssl_keyfile"] = str(key_path)
            app.state.server_state = ServerState.STARTING

    reload = args.reload
    if ssl_kw and reload:
        print(
            "  NOTE: --reload ignored with SSL "
            "(reloader subprocess loses SSL config)"
        )
        reload = False

    if ssl_kw:
        _orig_create_ssl = uvicorn.config.create_ssl_context

        def _hardened_ssl_context(
            certfile, keyfile, password, ssl_version,
            cert_reqs, ca_certs, ciphers,
        ):
            ctx = _orig_create_ssl(
                certfile, keyfile, password, ssl_version,
                cert_reqs, ca_certs, ciphers,
            )
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
            ctx.options |= ssl.OP_NO_COMPRESSION
            ctx.options |= ssl.OP_CIPHER_SERVER_PREFERENCE
            return ctx

        uvicorn.config.create_ssl_context = _hardened_ssl_context

    scheme = "https" if ssl_kw else "http"
    print("WebNC API starting...")
    print(f"  URL: {scheme}://{args.host}:{args.port}/")
    if ssl_kw:
        print(
            f"  SSL: TLS 1.3 forced (cert: {ssl_kw['ssl_certfile']})"
        )
    if args.insecure and args.host == "0.0.0.0":
        print(
            "  WARNING: Listening on 0.0.0.0 without SSL "
            "- data sent in plaintext!"
        )
    print("WebNC — multi-drive mode (C:, D:, ...)")
    sys.modules["webnc_server"] = sys.modules["__main__"]
    log_fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    log_datefmt = "%Y-%m-%d %H:%M:%S"
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_fmt,
                "datefmt": log_datefmt,
            },
            "access": {
                "format": log_fmt,
                "datefmt": log_datefmt,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
        },
    }

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=reload,
        log_config=log_config,
        **ssl_kw,
    )


if __name__ == "__main__":
    main()
