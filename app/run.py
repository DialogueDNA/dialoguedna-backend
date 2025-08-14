"""
run.py

Temporary launch script for running FastAPI via uvicorn from inside PyCharm.
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
