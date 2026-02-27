from dataclasses import dataclass
from enum import Enum
from typing import Optional

class OpType(str, Enum):
    START = "START"
    READ = "READ"
    WRITE = "WRITE"
    INC = "INC"
    DEC = "DEC"
    COMMIT = "COMMIT"
    ABORT = "ABORT"

@dataclass(frozen=True)
class Operation:
    optype: OpType
    tid: int
    item: Optional[str] = None  # None for START/COMMIT/ABORT
    raw: str = ""               # original token for nice error messages

    @property
    def is_write_like(self) -> bool:
        # project: inc/dec treated as write for conflict detection :contentReference[oaicite:18]{index=18}
        return self.optype in (OpType.WRITE, OpType.INC, OpType.DEC)

    @property
    def is_access(self) -> bool:
        return self.optype in (OpType.READ, OpType.WRITE, OpType.INC, OpType.DEC)