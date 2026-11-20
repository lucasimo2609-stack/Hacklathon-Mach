# The GP's prescription must match the protocol table (procedure AND priority): +2 when right,
# -1 when wrong. Runs whole GP turns in a fake city and checks what reaches the Ledger and the
# citizen. The expected table is written here on purpose (not read from the brain), so a change
# to _PROTOCOLS or to the symptom recognition that breaks the protocol fails this test.
import asyncio, sys, itertools
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01

PROTOCOL = {  # symptom code -> (procedure, priority), from the kit's protocol table
    "SYM-BACK": ("VIS-FIS", "B"),
    "SYM-KNEE": ("VIS-FIS", "D"),
    "SYM-PALPITATIONS": ("VIS-CARD", "B"),
    "SYM-FOLLOWUP": ("VIS-CARD", "P"),
}
CASES = [
    ("ho mal di schiena da settimane", "SYM-BACK"),
    ("my back hurts so much", "SYM-BACK"),
    ("colpo della strega stamattina", "SYM-BACK"),
    ("mi fa male il ginocchio", "SYM-KNEE"),
    ("Ho dolore al ginocchio destro quando salgo le scale", "SYM-KNEE"),
    ("my knee hurts", "SYM-KNEE"),
    ("ho le palpitazioni", "SYM-PALPITATIONS"),
    ("il cuore mi va a mille", "SYM-PALPITATIONS"),
    ("my heart is racing", "SYM-PALPITATIONS"),
    ("vorrei fare un controllo del cuore di routine", "SYM-FOLLOWUP"),
    ("routine heart check please", "SYM-FOLLOWUP"),
]

ids = itertools.count(1); GP = "agent:gp"; CIT = "citizen:t/3"


class C:
    def __init__(s): s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.inbound = None
    agent_id = property(lambda s: GP); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None): s.add(GP, to, text); s.out.append((to, text))
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")


def fields(text):
    return dict(p.split("=", 1) for p in text.split() if "=" in p)


async def check(text, code):
    c = C(); m = c.add(CIT, GP, text); c.inbound = m
    await A.handle("gp", c, m, await c.history())
    want_proc, want_prio = PROTOCOL[code]
    problems = []
    ledger = [t for to, t in c.out if to == LEDGER and t.startswith("prescribe ")]
    citizen = [t for to, t in c.out if to == CIT and "prescription_number=" in t]
    if len(ledger) != 1:
        problems.append(f"{len(ledger)} prescribe lines to the Ledger")
    for t in ledger:
        f = fields(t)
        if (f.get("procedure"), f.get("priority"), f.get("symptom_code")) != (want_proc, want_prio, code):
            problems.append(f"ledger {f.get('symptom_code')} {f.get('procedure')}/{f.get('priority')}")
    if not citizen:
        problems.append("citizen got no prescription")
    for t in citizen:
        f = fields(t)
        if (f.get("procedure"), f.get("priority")) != (want_proc, want_prio):
            problems.append(f"citizen {f.get('procedure')}/{f.get('priority')}")
    if any(to == LEDGER and t.startswith("escalate") for to, t in c.out):
        problems.append("escalated a non-red-flag symptom")
    print("OK " if not problems else "BAD", repr(text)[:55], "->", want_proc, want_prio, "|", "; ".join(problems))
    return not problems


async def main():
    # Every protocol row must be covered by at least one case.
    missing = set(PROTOCOL) - {code for _, code in CASES}
    bad = len(missing)
    if missing:
        print("BAD protocol rows without a case:", sorted(missing))
    # The brain's table must say the same as the protocol.
    for code, row in PROTOCOL.items():
        if A._PROTOCOLS.get(code) != row:
            print("BAD _PROTOCOLS", code, A._PROTOCOLS.get(code), "want", row); bad += 1
    for text, code in CASES:
        bad += not await check(text, code)
    print("failures:", bad)
    sys.exit(1 if bad else 0)


asyncio.run(main())
