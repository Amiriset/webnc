"""
WebNC — Backend API Server (thin shim)
=======================================
This file is kept for backward compatibility.
All logic has been refactored into the ``webnc/`` package.

Usage:
    uvicorn webnc_server:app --reload --port 8000
    python webnc_server.py [--host ...] [--port ...] [--insecure]
"""

from webnc.main import app, main

if __name__ == "__main__":
    main()
