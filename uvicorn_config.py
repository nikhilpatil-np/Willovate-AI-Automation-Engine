"""
uvicorn_config.py
=================
Custom uvicorn entry point that forces ProactorEventLoop on Windows
before uvicorn touches the event loop.

Use this instead of `uvicorn main:app` on Windows:

    python uvicorn_config.py

This is necessary because Playwright requires asyncio.create_subprocess_exec
which only works on Windows with ProactorEventLoop, but uvicorn's default
SelectorEventLoop does not support it.
"""

import sys
import asyncio

# Must be set BEFORE uvicorn is imported/run
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,           # reload=True spawns a subprocess which resets the loop — keep False
        loop="asyncio",         # tell uvicorn to use the asyncio backend (respects our policy)
        log_level="info",
    )
