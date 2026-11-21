"""Facility with a slow Ledger (21 Nov, wave W01QQQ: 25 confirms on our own facilities, the
booking centre said "la ricevuta arriva tra pochi secondi" and no receipt ever came). The Ledger
answers hold and commit after DELAY seconds and the late answers do NOT open a turn: the confirm
turn itself must still commit and send exactly one receipt. Run:
tests/h_slow_hold.py hospital/agent hospital"""
import asyncio, sys, itertools, os, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01  # budget scales to 15 s, poll 0.2 s
ids = itertools.count(1); ME = "agent:hosp"; BC = "agent:cdc7x6m21nj6"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
class C:
    def __init__(s, delay, refuse=False):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.delay = delay; s.refuse = refuse
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(ME, to, text); s.out.append((to, text))
        if to == LEDGER:
            f = A.fields_of(text); h = text.split()[0]
            async def later(line):
                await asyncio.sleep(s.delay); s.add(LEDGER, ME, line)
            if h == "hold":
                line = "refused op=hold code=SLOT_TAKEN" if s.refuse else f"held hold_id=H-{s.need} slot_id={f['slot_id']}"
                asyncio.ensure_future(later(line))
            if h == "commit":
                asyncio.ensure_future(later(f"committed booking_id={f['hold_id']} ledger_ref=L1 slot_id=S2"))
        return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
async def confirm(c, role):
    c.add(ME, BC, "offer offer_id=of-S2 slot_id=S2 doctor_id=asst-giambellino-h1 facility=agent:hosp procedure=VIS-FIS agenda_date=2026-11-03T10:30:00 request_id=N-9")
    m = c.add(BC, ME, "confirm offer_id=of-S2 slot_id=S2 citizen=citizen:t/5 consent_ref=cons-N-9-booking facility=agent:hosp prescription_number=rx-9 request_id=N-9")
    t = time.monotonic()
    await A.handle(role, c, m, await c.history())
    return time.monotonic() - t
async def main(role):
    c = C(delay=8.0)
    took = await confirm(c, role)
    led = [t for to, t in c.out if to == LEDGER]
    rec = [t for to, t in c.out if to == BC and t.startswith("booking.receipt")]
    check("Ledger 8 s late on hold and commit: one hold, one commit", sum(x.startswith("hold ") for x in led) == 1 and sum(x.startswith("commit ") for x in led) == 1, str(led))
    check("Ledger 8 s late: exactly one receipt to the booking centre, same turn", len(rec) == 1, str(c.out))
    check("Ledger 8 s late: turn bounded by the patient budget", took < 40, f"{took:.1f}s")
    # The late "held" also opens its own turn while the first one waits: still one commit.
    c = C(delay=3.0)
    task = asyncio.ensure_future(confirm(c, role))
    await asyncio.sleep(3.5)
    held = next((r for r in c.rows if r.sender == LEDGER and r.text.startswith("held")), None)
    if held is not None:
        await A.handle(role, c, held, await c.history())
    await task
    led = [t for to, t in c.out if to == LEDGER]
    rec = [t for to, t in c.out if to == BC and t.startswith("booking.receipt")]
    check("late held opens a turn too: still one commit", sum(x.startswith("commit ") for x in led) == 1, str(led))
    check("late held opens a turn too: one receipt", len(rec) == 1, str(rec))
    # A late refusal still reaches the booking centre (no silent stall).
    c = C(delay=4.0, refuse=True)
    await confirm(c, role)
    to_bc = [t for to, t in c.out if to == BC]
    check("late refusal: the booking centre hears about it", any(t.startswith("cancel") or "slot_taken" in t or "offer " in t for t in to_bc), str(to_bc))
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
