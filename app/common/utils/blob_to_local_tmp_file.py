import os, tempfile, requests
from contextlib import contextmanager

@contextmanager
def download_to_tmp_file(url: str, suffix: str = ""):
    """
    Stream-download `url` to a temp file, yield its path, and delete it on exit.
    Use suffix like '.wav' if consumers rely on extension.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # we'll reopen normally
    try:
        with requests.get(url, stream=True) as r, open(path, "wb") as f:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        yield path
    finally:
        try: os.remove(path)
        except FileNotFoundError: pass
