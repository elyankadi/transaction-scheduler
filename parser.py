import re
from typing import List
from model import Operation, OpType

RE_START = re.compile(r"^s(\d+)$", re.IGNORECASE)
RE_END   = re.compile(r"^(c|a)(\d+)$", re.IGNORECASE)
RE_RW    = re.compile(r"^(r|w)(\d+)\[([A-Za-z]\w*)\]$", re.IGNORECASE)
RE_INCDEC= re.compile(r"^(inc|dec)(\d+)\[([A-Za-z]\w*)\]$", re.IGNORECASE)

# NEW: Formal notation support
RE_FORMAL_START = re.compile(r"^start\(t?(\d+)\)$", re.IGNORECASE)
RE_FORMAL_END = re.compile(r"^(commit|abort)\(t?(\d+)\)$", re.IGNORECASE)
RE_FORMAL_RW = re.compile(r"^(read|write)\(t?(\d+),\s*([A-Za-z]\w*)\)$", re.IGNORECASE)
RE_FORMAL_INCDEC = re.compile(r"^(increment|decrement)\(t?(\d+),\s*([A-Za-z]\w*)\)$", re.IGNORECASE)

def parse_ops(op_string: str) -> List[Operation]:
    tokens = [t.strip() for t in re.split(r"[,\s]+", op_string.strip()) if t.strip()]
    ops: List[Operation] = []

    for tok in tokens:
        tok = tok.lower()  # 🔥 IMPROVEMENT 1: normalize tokens

        # Shorthand START (s1)
        m = RE_START.match(tok)
        if m:
            tid = int(m.group(1))
            ops.append(Operation(OpType.START, tid, None, tok))
            continue

        # Formal START (start(t1) or start(1))
        m = RE_FORMAL_START.match(tok)
        if m:
            tid = int(m.group(1))
            ops.append(Operation(OpType.START, tid, None, tok))
            continue

        # Shorthand COMMIT/ABORT (c1 / a1)
        m = RE_END.match(tok)
        if m:
            kind, tid = m.group(1).lower(), int(m.group(2))
            ops.append(Operation(OpType.COMMIT if kind == "c" else OpType.ABORT, tid, None, tok))
            continue

        # Formal COMMIT/ABORT (commit(t1), abort(1))
        m = RE_FORMAL_END.match(tok)
        if m:
            kind, tid = m.group(1).lower(), int(m.group(2))
            ops.append(Operation(OpType.COMMIT if kind == "commit" else OpType.ABORT, tid, None, tok))
            continue

        # Shorthand READ/WRITE (r1[x], w2[y])
        m = RE_RW.match(tok)
        if m:
            kind, tid, item = m.group(1).lower(), int(m.group(2)), m.group(3)
            ops.append(Operation(OpType.READ if kind == "r" else OpType.WRITE, tid, item, tok))
            continue

        # Formal READ/WRITE (read(t1,x), write(2,y))
        m = RE_FORMAL_RW.match(tok)
        if m:
            kind, tid, item = m.group(1).lower(), int(m.group(2)), m.group(3)
            ops.append(Operation(OpType.READ if kind == "read" else OpType.WRITE, tid, item, tok))
            continue

        # Shorthand INC/DEC (inc1[x], dec2[y])
        m = RE_INCDEC.match(tok)
        if m:
            kind, tid, item = m.group(1).lower(), int(m.group(2)), m.group(3)
            ops.append(Operation(OpType.INC if kind == "inc" else OpType.DEC, tid, item, tok))
            continue

        # Formal INC/DEC (increment(t1,x), decrement(2,y))
        m = RE_FORMAL_INCDEC.match(tok)
        if m:
            kind, tid, item = m.group(1).lower(), int(m.group(2)), m.group(3)
            ops.append(Operation(OpType.INC if kind == "increment" else OpType.DEC, tid, item, tok))
            continue

        raise ValueError(
            f"Invalid token '{tok}'. Supported formats:\n"
            f"- s1, c1, a1\n"
            f"- r1[x], w2[y], inc3[z], dec1[x]\n"
            f"- start(t1), read(t1,x), write(t2,y), increment(t1,x), commit(t1)"
        )

    return ops