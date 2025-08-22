from dataclasses import dataclass
from typing import Union, Optional

Writer = Union[str, int]  # e.g. "John Doe"/1
TextType = str

@dataclass
class TextSegment:
    text:       TextType
    writer:     Optional[Writer]   = None
    start_time: Optional[float]    = None
    end_time:   Optional[float]    = None
    language:   Optional[str]      = None