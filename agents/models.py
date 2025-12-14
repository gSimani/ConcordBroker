from dataclasses import dataclass, field
from typing import Optional, Dict


@dataclass
class Task:
    dataset: str  # NAL | SDF | NAP
    year: int
    county: Optional[str] = None
    ticket: Optional[str] = None
    url: Optional[str] = None
    release: Optional[str] = None  # F|P
    version: Optional[int] = None
    local_path: Optional[str] = None
    status: str = "pending"  # pending|running|done|failed
    attempts: int = 0
    meta: Dict = field(default_factory=dict)

