# app/tests/audio/debug_convert.py
from pathlib import Path
import shutil
import sys

from app.services.audio.processor.ffutils import (
    ensure_ffmpeg_tools, probe_format, needs_pcm16_mono_16k
)
from app.services.audio.processor.audio_processor import AudioProcessor
from app.core.config import (
    SAMPLE_RATE as TARGET_SAMPLE_RATE,
    TARGET_CHANNELS, TARGET_CONTAINER, TARGET_CODEC
)

RAW_DIR = Path(__file__).parent / "data" / "raw"
FIXED_DIR = Path(__file__).parent / "data" / "fixed"
FILE_NAME = "angry_client.mpeg"  # <--- change to your test file name   *****IMPORTANT : only chance here the file *****

def main():
    try:
        ensure_ffmpeg_tools()
    except Exception as e:
        print(f"[ERROR] ffmpeg/ffprobe missing: {e}")
        sys.exit(1)

    FIXED_DIR.mkdir(parents=True, exist_ok=True)

    src = RAW_DIR / FILE_NAME
    if not src.exists():
        print(f"[ERROR] Missing input file: {src}")
        sys.exit(1)

    print(f"[INFO] Source: {src}")
    src_meta = probe_format(src)
    print(f"[INFO] Source meta: {src_meta}")
    print(f"[INFO] Needs conversion? {needs_pcm16_mono_16k(src_meta)}")

    proc = AudioProcessor(temp_dir=FIXED_DIR)
    ready_path, meta = proc.prepare_path(src)  # sync path-based flow (debug-friendly)
    print(f"[INFO] Ready path: {ready_path}")
    print(f"[INFO] Meta after prepare: {meta}")

    # ensure file lands in FIXED_DIR (copy if needed)
    if ready_path.parent != FIXED_DIR:
        dst = FIXED_DIR / ready_path.name
        shutil.copy2(ready_path, dst)
        ready_path = dst
        print(f"[INFO] Copied to: {ready_path}")

    # verify target specs
    out_meta = probe_format(ready_path)
    ok = (
        out_meta["container"] == TARGET_CONTAINER and
        out_meta["codec"] == TARGET_CODEC and
        out_meta["channels"] == TARGET_CHANNELS and
        out_meta["sample_rate"] == TARGET_SAMPLE_RATE and
        ready_path.suffix.lower() == ".wav"
    )
    if ok:
        status = "SUCCESS (converted)" if meta.get("was_converted") else "ALREADY OK (no conversion needed)"
        print(f"[OK] {status}. Output @ {ready_path}")
    else:
        print(f"[FAIL] Output format mismatch: {out_meta}")
        sys.exit(2)

if __name__ == "__main__":
    main()
