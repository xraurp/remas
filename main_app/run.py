#!/usr/bin/env python3
if __name__ == "__main__":
    """
    This runs the FastAPI server. App is defined in main.py.
    For development `fastapi dev src/main.py` command can be used instead.
    """
    import uvicorn
    import os
    from src.config import Settings

    settings = Settings()

    uvicorn.run(
        app="src.main:app",
        host=settings.host,
        port=settings.port
    )
