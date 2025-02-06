#!/usr/bin/env python3
if __name__ == "__main__":
    """
    This runs the FastAPI server. App is defined in main.py.
    For development `fastapi dev main.py` command can be used instead.
    """
    import uvicorn
    import os

    # Get host and port from environment variables
    host = os.environ.get("HOST", "0.0.0.0")
    port = os.environ.get("PORT", 8000)

    uvicorn.run(
        app="main:app",
        host=host,
        port=port
    )
