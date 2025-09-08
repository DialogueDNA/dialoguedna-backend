# pdf.py
"""
Generate a Unicode-safe PDF for a session summary.

- Uses a TrueType font (e.g., DejaVuSans.ttf) with `uni=True` so Hebrew/Arabic/Emoji render correctly.
- Keeps the same public function name/signature: generate_session_pdf(session: dict) -> str
- Creates the PDF in the system temp directory and returns the full path.

Expected keys in `session` dict:
    - id: str
    - title: str | None
    - created_at: str | datetime | None
    - duration: str | int | None
    - participants: list[str] | None
    - summary: str | None
"""

from __future__ import annotations
from fpdf import FPDF
from pathlib import Path
from uuid import uuid4
import tempfile
from typing import Optional, Iterable, Any

# Default font file name to look for next to this module
_DEFAULT_FONT_NAME = "DejaVuSans.ttf"


class _UnicodePDF(FPDF):
    """FPDF subclass with a helper to load a TTF font once."""
    _font_loaded: bool = False

    def ensure_unicode_font(self, font_path: Optional[str] = None, size: int = 12):
        """
        Load a TrueType font with uni=True exactly once. Falls back to core font if missing (ASCII only).
        """
        if self._font_loaded:
            self.set_font("DejaVu", size=size)
            return

        ttf_path: Optional[Path] = None
        if font_path:
            ttf_path = Path(font_path)
        else:
            # Try to load bundled font from the same directory as this file
            ttf_path = Path(__file__).parent.joinpath(_DEFAULT_FONT_NAME)
            if not ttf_path.exists():
                ttf_path = None

        if ttf_path and ttf_path.exists():
            # Load a Unicode TTF
            self.add_font("DejaVu", "", str(ttf_path), uni=True)
            self.set_font("DejaVu", size=size)
            self._font_loaded = True
        else:
            # Fallback: core fonts (no Unicode support). Better than crashing.
            self.set_font("Arial", size=size)


def _as_text(value: Any) -> str:
    return "" if value is None else str(value)


def _join(values: Optional[Iterable[str]], sep: str = ", ") -> str:
    if not values:
        return ""
    return sep.join(v for v in values if isinstance(v, str) and v.strip())


def generate_session_pdf(session: dict, font_path: Optional[str] = None) -> str:
    """
    Generate a PDF file for the given session and return its absolute path.
    """
    pdf = _UnicodePDF()
    pdf.add_page()
    pdf.ensure_unicode_font(font_path=font_path, size=13)

    # Header / title
    title = _as_text(session.get("title")).strip()
    if title:
        pdf.set_font_size(16)
        pdf.cell(0, 10, txt=f"Session Title: {title}", ln=True)
        pdf.set_font_size(13)
    else:
        pdf.cell(0, 10, txt="Session", ln=True)

    # Meta
    created_at = session.get("created_at")
    duration = session.get("duration")
    participants = session.get("participants")

    if created_at:
        pdf.cell(0, 8, txt=f"Created at: {_as_text(created_at)}", ln=True)
    if duration:
        pdf.cell(0, 8, txt=f"Duration: {_as_text(duration)}", ln=True)
    parts_line = _join(participants)
    if parts_line:
        pdf.cell(0, 8, txt=f"Participants: {parts_line}", ln=True)

    # Divider
    pdf.ln(4)
    pdf.cell(0, 8, txt="Summary:", ln=True)

    # Body text (summary)
    summary_text = _as_text(session.get("summary")).strip() or "Summary not yet generated"
    # Slightly tighter line height for long texts
    pdf.multi_cell(0, 7.5, txt=summary_text)

    # Output file in temp dir
    tmp_dir = Path(tempfile.gettempdir())
    filename = f"session-{_as_text(session.get('id') or 'unknown')}-{uuid4().hex}.pdf"
    output_path = str(tmp_dir / filename)
    pdf.output(output_path)

    return output_path
