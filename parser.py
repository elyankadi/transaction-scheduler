import re
from typing import List
from model import Operation, OpType

RE_START = re.compile(r"^s(\d+)$", re.IGNORECASE)
RE_END   = re.compile(r"^(c|a)(\d+)$", re.IGNORECASE)
RE_RW    = re.compile(r"^(r|w)(\d+)\[([A-Za-z]\w*)\]$", re.IGNORECASE)
RE_INCDEC= re.compile(r"^(inc|dec)(\d+)\[([A-Za-z]\w*)\]$", re.IGNORECASE)

def parse_ops(op_string: str) -> List[Operation]:
    tokens = [t.strip() for t in re.split(r"[,\s]+", op_string.strip()) if t.strip()]
    ops: List[Operation] = []

    for tok in tokens:
        m = RE_START.match(tok)
        if m:
            tid = int(m.group(1))
            ops.append(Operation(OpType.START, tid, None, tok))
            continue

        m = RE_END.match(tok)
        if m:
            kind, tid = m.group(1).lower(), int(m.group(2))
            ops.append(Operation(OpType.COMMIT if kind == "c" else OpType.ABORT, tid, None, tok))
            continue

        m = RE_RW.match(tok)
        if m:
            kind, tid, item = m.group(1).lower(), int(m.group(2)), m.group(3)
            ops.append(Operation(OpType.READ if kind == "r" else OpType.WRITE, tid, item, tok))
            continue

        m = RE_INCDEC.match(tok)
        if m:
            kind, tid, item = m.group(1).lower(), int(m.group(2)), m.group(3)
            ops.append(Operation(OpType.INC if kind == "inc" else OpType.DEC, tid, item, tok))
            continue

        raise ValueError(f"Invalid token '{tok}'. Expected like: s1, r1[x], w2[y], inc3[z], dec1[x], c1, a2")

    return ops