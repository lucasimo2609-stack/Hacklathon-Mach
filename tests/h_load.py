"""Load control on facilities (21 Nov 13:50: requests between agents queued up).
1. A partner request whose own deadline is behind the agenda clock: closed at once
   (cancel reason=outside_window), no Ledger trip.
2. A partner request that queued > 10 min, Ledger silent: answered from a 20-min-old copy at
   once, no long wait.
3. Busy (>= _BUSY_AT turns waiting): a hold wait gets a fifth of its budget.
4. _age() reads sent_at; a missing stamp is not 'old'.
Run: tests/h_load.py hospital/agent hospital"""
import asyncio, sys, itertools, os, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from datetime import datetime, timedelta, timezone
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); ME = "agent:h6r1v45esk77"; PBC = "agent:psxp8bh1feaa"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
def iso(dt): return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
def line(i, at):
    return f"slot_id=L{i} doctor_id=asst-giambellino-h1 facility={ME} procedure=VIS-FIS at={at}:00+00:00 day=wed free=1"
class C:
    def __init__(s, silent=True):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.silent = silent
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t, sent_at=""):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b, sent_at=sent_at)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(ME, to, text); s.out.append((to, text)); return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
def warm(age_s):
    A._WORLD_SEEN.clear(); A._INFLIGHT = 0
    A._FAC_WORLD_ASKED["VIS-FIS"] = time.monotonic()  # keep the list-warming request out of these checks
    A._AGENDA_SEEN = (time.monotonic(), datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc))
    if age_s is not None:
        A._WORLD_SEEN["VIS-FIS"] = (time.monotonic() - age_s, "slots page=1/1\n" + line(1, "2026-11-04T10:30"))
async def main(role):
    now_real = datetime.now(timezone.utc)
    # 1. deadline already behind the agenda clock
    warm(None); c = C()
    m = c.add(PBC, ME, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B deadline=2026-11-03T06:00 request_id=R-1", iso(now_real))
    t0 = time.monotonic(); await A.handle(role, c, m, await c.history()); took = time.monotonic() - t0
    to_p = [t for to, t in c.out if to == PBC]; led = [t for to, t in c.out if to == LEDGER]
    check("expired deadline: cancel reason=outside_window", any("reason=outside_window" in t and "request_id=R-1" in t for t in to_p), str(to_p))
    check("expired deadline: no Ledger trip, instant", not led and took < 1, f"{took:.2f}s {led}")
    # 2. queued 15 min, Ledger silent, 20-min-old copy
    warm(1200); c = C()
    m = c.add(PBC, ME, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D request_id=R-2", iso(now_real - timedelta(minutes=15)))
    t0 = time.monotonic(); await A.handle(role, c, m, await c.history()); took = time.monotonic() - t0
    to_p = " // ".join(t for to, t in c.out if to == PBC)
    check("queued 15 min: offer from the copy", "offer offer_id=of-L1" in to_p, to_p)
    check("queued 15 min: no long wait", took < 1.5, f"{took:.2f}s")
    # 3. same request, fresh, Ledger silent, only an old copy: waits the (scaled) budget, then copy
    warm(1200); c = C()
    m = c.add(PBC, ME, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D request_id=R-3", iso(now_real))
    t0 = time.monotonic(); await A.handle(role, c, m, await c.history()); took_fresh = time.monotonic() - t0
    warm(1200); A._INFLIGHT = A._BUSY_AT; c = C()
    m = c.add(PBC, ME, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D request_id=R-4", iso(now_real))
    t0 = time.monotonic(); await A.handle(role, c, m, await c.history()); took_busy = time.monotonic() - t0
    A._INFLIGHT = 0
    check("busy: the partner turn ends much sooner than when idle", took_busy < took_fresh / 2, f"busy {took_busy:.2f}s idle {took_fresh:.2f}s")
    check("busy: still answers from the copy", "offer offer_id=of-L1" in " ".join(t for to, t in c.out if to == PBC), str(c.out))
    # 4. budgets and age
    A._INFLIGHT = 0; full = A._budget(100.0); A._INFLIGHT = A._BUSY_AT; busy = A._budget(100.0); A._INFLIGHT = 0
    check("budget: full when idle, a fifth when busy", full == 100.0 and busy == 20.0, f"{full} {busy}")
    old = Message(type="chat", sender=PBC, msg_id="x", sent_at=iso(now_real - timedelta(minutes=12)))
    none = Message(type="chat", sender=PBC, msg_id="y")
    check("_age reads sent_at (12 min)", 700 < (A._age(old) or 0) < 740, str(A._age(old)))
    check("_age without a stamp is None (never 'old')", A._age(none) is None, str(A._age(none)))
    check("counter back to zero after the waits", A._INFLIGHT == 0, str(A._INFLIGHT))
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
