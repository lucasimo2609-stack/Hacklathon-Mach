"""Facilities keep their own slot list warm (21 Nov 15:05: the booking's direct channel got
'ledger_slow' because no facility held a copy, then the booking sent a waiting list the
citizen refused).
1. Any facility turn with no recent copy asks the Ledger for its own list (no wait).
2. Not again within 2 minutes; not at all when the copy is fresh.
3. The Ledger's late answer, arriving in another case, becomes the copy, and the next
   request from our booking (source=own_asst) gets real offers at once.
Run: tests/h_warm.py hospital/agent hospital"""
import asyncio, sys, itertools, os, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from datetime import datetime, timezone
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); ME = "agent:h6r1v45esk77"; BC = "agent:cdc7x6m21nj6"; CIT = "citizen:t/1"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
class C:
    def __init__(s):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(ME, to, text); s.out.append((to, text)); return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
def worlds(c): return [t for to, t in c.out if to == LEDGER and t.startswith("world procedure=VIS-FIS")]
async def main(role):
    A._WORLD_SEEN.clear(); A._FAC_WORLD_ASKED.clear(); A._INFLIGHT = 0
    A._AGENDA_SEEN = (time.monotonic(), datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc))
    # 1. a citizen's check-in question with no copy -> one world request
    c = C(); await A.handle(role, c, c.add(CIT, ME, "sono arrivato, dove devo andare?"), await c.history())
    check("no copy: the facility asks the Ledger for its own list", len(worlds(c)) == 1, str(c.out))
    # 2. another turn right after: no second request
    c2 = C(); await A.handle(role, c2, c2.add(CIT, ME, "buongiorno"), await c2.history())
    check("within 2 min: no second request", not worlds(c2), str(c2.out))
    # 3. the late answer lands in a case: next turn keeps it as the copy
    c3 = C()
    c3.add(LEDGER, ME, "slots page=1/1\nslot_id=WW1 doctor_id=asst-giambellino-h1 facility=agent:h6r1v45esk77 procedure=VIS-FIS at=2026-11-04T10:30:00+00:00 day=wed free=1")
    m = c3.add(LEDGER, ME, "agenda agenda_now=2026-11-03T08:00:00+00:00")
    await A.handle(role, c3, m, await c3.history())
    check("late Ledger answer kept as the copy", "VIS-FIS" in A._WORLD_SEEN, str(list(A._WORLD_SEEN)))
    # 4. our booking asks directly: real offers at once from the copy
    c4 = C(); t0 = time.monotonic()
    req = c4.add(BC, ME, "need.request procedure=VIS-FIS priority=D request_id=N-own source=own_asst Richiesta interna")
    await A.handle(role, c4, req, await c4.history()); took = time.monotonic() - t0
    to_bc = " // ".join(t for to, t in c4.out if to == BC)
    check("own booking gets offers from the warmed copy", "offer offer_id=of-WW1" in to_bc, to_bc)
    check("...at once", took < 1.0, f"{took:.2f}s")
    check("fresh copy: no new world request", not worlds(c4), str(c4.out))
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
