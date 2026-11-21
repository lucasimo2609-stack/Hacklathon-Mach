"""Facilities with a slow Ledger and the learned reply lead (21 Nov, wave W01QQQ).
1. A partner's need.request while the Ledger answers late: offers, never a blind
   'no_availability' after 6 s (partners dropped us).
2. A citizen calls an offer past: from then on planned slots that close are not offered.
3. Consultorio: page 1 all behind the lead -> read the next page, not the waiting list.
Run: tests/h_partner_slow.py hospital/agent hospital"""
import asyncio, sys, itertools, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from datetime import datetime, timedelta
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); ME = "agent:h6r1v45esk77"; PBC = "agent:psxp8bh1feaa"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
def line(i, at, doc="asst-giambellino-h1", fac=ME):
    day = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[datetime.fromisoformat(at).weekday()]
    return f"slot_id=P{i} doctor_id={doc} facility={fac} procedure=VIS-FIS at={at}:00+00:00 day={day} free=1"
class C:
    def __init__(s, slots, delay):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.slots = slots; s.delay = delay
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(ME, to, text); s.out.append((to, text))
        if to == LEDGER:
            h = text.split()[0]
            async def later(t):
                await asyncio.sleep(s.delay); s.add(LEDGER, ME, t)
            if h == "agenda": asyncio.ensure_future(later("agenda agenda_now=2026-11-03T08:00:00+00:00"))
            if h == "world": asyncio.ensure_future(later("slots page=1/1\n" + "\n".join(s.slots)))
        return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
def reset():
    A._WORLD_SEEN.clear(); A._AGENDA_SEEN = None; A._LEARNED_LEAD = timedelta(0); A._OFFER_NOW.clear()
async def main(role):
    reset()
    c = C([line(1, "2026-11-04T10:30"), line(2, "2026-11-04T12:00")], delay=3.0)
    m = c.add(PBC, ME, "need.request mach=1.4 service_type=hospital.physiatry procedure=VIS-FIS priority=B lang=it request_id=R-1")
    await A.handle(role, c, m, await c.history())
    sent = [t for to, t in c.out if to == PBC]
    joined = " // ".join(sent)
    check("Ledger 3 s late: partner gets our offers", "offer offer_id=of-P1" in joined, joined)
    check("Ledger 3 s late: no blind no_availability", "no_availability" not in joined, joined)
    led = [t.split()[0] for to, t in c.out if to == LEDGER]
    check("agenda and world asked (in parallel with the ack)", "agenda" in led and "world" in led, str(led))
    # Learned lead: an offer 6 h ahead was called past -> lead >= 7 h for planned priorities.
    reset()
    now = datetime(2026, 11, 3, 8, 0, tzinfo=A.timezone.utc) if hasattr(A, "timezone") else datetime(2026, 11, 3, 8, 0)
    A._OFFER_NOW["P9"] = now
    A._learn_past("P9", now + timedelta(hours=6))
    check("learned lead after a 'past' 6 h out: >= 7 h", A._LEARNED_LEAD >= timedelta(hours=7), str(A._LEARNED_LEAD))
    lines = [line(3, "2026-11-03T12:00"), line(4, "2026-11-03T16:00"), line(5, "2026-11-04T10:30")]
    got = [s["slot_id"] for s in A.fitting(lines, now=now, priority="B", lang="it")]
    check("planned B: slots inside the learned lead skipped", got == ["P4", "P5"] or got == ["P5"], str(got))
    got_u = [s["slot_id"] for s in A.fitting(lines, now=now, priority="U", lang="it")]
    check("U unchanged: same-day slots still offered", "P3" in got_u, str(got_u))
    A._learn_past("P-none", now + timedelta(hours=40))  # unknown offer: ignored
    A._OFFER_NOW["P8"] = now; A._learn_past("P8", now + timedelta(hours=40))  # beyond the cap: ignored
    check("absurd gaps ignored (cap 24 h)", A._LEARNED_LEAD < timedelta(hours=24), str(A._LEARNED_LEAD))
    # Consultorio paging: a full page 1 that is all behind the lead is not "enough choice".
    reset()
    page = "\n".join(line(10 + i, f"2026-11-03T0{8 + (i % 2)}:{'00' if i < 5 else '30'}") for i in range(10))
    check("page 1 all behind 'now + lead' -> read more pages", A._need_more_pages(page, datetime(2026, 11, 3, 10, 0, tzinfo=A.timezone.utc), None), "")
    future = "\n".join(line(20 + i, f"2026-11-0{4 + i // 5}T{10 + i % 5}:00") for i in range(10))
    check("page 1 with 10 slots ahead -> enough", not A._need_more_pages(future, datetime(2026, 11, 3, 10, 0, tzinfo=A.timezone.utc), None), "")
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
