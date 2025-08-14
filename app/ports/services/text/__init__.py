from dataclasses import dataclass
from typing import Union, Optional

Writer = Union[str, int]  # e.g. "John Doe"/1
TextType = str

@dataclass
class TextSegment:
    """
    Input for the text segment.
    Represents a segment of text with optional start and end times.
    """
    writer: Optional[Writer]
    text: TextType
    start_time: Optional[float]
    end_time: Optional[float]
    language: Optional[str]