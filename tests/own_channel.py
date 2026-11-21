"""Booking centre + our own hospital, both REAL brains in one fake city (bc_own fakes the
hospital's answer, so it never saw that the hospital dropped the request).
1. Ledger slow 40 s, hospital holds a slot copy: the booking asks the hospital at once and the
   citizen gets our offers within seconds, no "no slot in our ASST", no partner search.
2. Ledger slow, hospital has NO copy: the hospital says ledger_slow (not no_availability); the
   booking waits for the Ledger and offers its slot, no partner search, no waiting list.
Run: tests/own_channel.py booking_centre/agent"""
import asyncio, sys, itertools, time, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from datetime import datetime, timezone
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
A._SLOW_WAIT = 4.0; A._SLOW_REASK = 2.0; A._SLOW_POLL = 0.05
ids = itertools.count(1)
BC = "agent:cdc7x6m21nj6"; HOSP = "agent:h6r1v45esk77"; CIT = "citizen:t/1"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
def line(i, at, doc="asst-giambellino-h1"):
    return f"slot_id=W{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={at}:00+00:00 day=wed free=1"
class City:
    """One shared case; each agent sees it through its own handle."""
    def __init__(s, ledger_delay):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.delay = ledger_delay; s.tasks = []
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    def handle_for(s, me, role):
        city = s
        class H:
            agent_id = me; address = ""
            async def say(self, to, text, status=None):
                city.add(me, to, text); city.out.append((me, to, text))
                if to == LEDGER: city.ledger(me, text)
                if to == HOSP and me == BC:
                    m = city.rows[-1]
                    os.environ["CITY_ROLE"] = "hospital"
                    city.tasks.append(asyncio.ensure_future(A.handle("hospital", city.handle_for(HOSP, "hospital"), m, list(city.rows))))
                return "x"
            async def history(self, peer=None, *, need_id=None): return list(city.rows)
            async def find(self, q): return []
            async def llm(self, *a, **k): raise CapError("KEY_UNKNOWN", "x")
        return H()
    def ledger(s, me, text):
        f = A.fields_of(text); h = text.split()[0]
        def later(t):
            async def go():
                await asyncio.sleep(s.delay); s.add(LEDGER, me, t)
            asyncio.ensure_future(go())
        if h == "prescription":
            s.add(LEDGER, me, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=D state=issued")
        elif h == "agenda":
            s.add(LEDGER, me, "agenda agenda_now=2026-11-03T08:00:00+00:00")
        elif h == "world":
            later("slots page=1/1\n" + line(9, "2026-11-05T10:30"))
def reset(copy):
    A._WORLD_SEEN.clear(); A._INFLIGHT = 0; A._DOWN.clear()
    A._AGENDA_SEEN = (time.monotonic(), datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc))
    if copy:
        A._WORLD_SEEN["VIS-FIS"] = (time.monotonic() - 300, "slots page=1/1\n" + line(1, "2026-11-04T10:30") + "\n" + line(2, "2026-11-04T12:00"))
async def run(copy, delay=40.0):
    reset(copy); c = City(ledger_delay=delay)
    m = c.add(CIT, BC, "vorrei prenotare la visita prescription_number=rx-1 lang=it")
    os.environ["CITY_ROLE"] = "booking_centre"
    t0 = time.monotonic()
    turn = asyncio.ensure_future(A.handle("booking_centre", c.handle_for(BC, "booking_centre"), m, list(c.rows)))
    first = None
    while not turn.done() and time.monotonic() - t0 < 30:
        await asyncio.sleep(0.05)
        if first is None and any(me == BC and to == CIT and "offer offer_id=of-W" in t for me, to, t in c.out):
            first = time.monotonic() - t0
    await asyncio.wait_for(turn, 60)
    for t in c.tasks:
        try: await asyncio.wait_for(t, 10)
        except Exception: pass
    to_cit = " // ".join(t for me, to, t in c.out if me == BC and to == CIT)
    to_bc = [t for me, to, t in c.out if me == HOSP and to == BC]
    asked = [t for me, to, t in c.out if me == BC and to == HOSP]
    return first, to_cit, to_bc, asked
async def main():
    first, to_cit, to_bc, asked = await run(copy=True)
    check("copy: booking asked our hospital directly", any(t.startswith("need.request") and "source=own_asst" in t for t in asked), str(asked))
    check("copy: the hospital answered with offers", any("offer offer_id=of-W1" in t for t in to_bc), str(to_bc))
    check("copy: citizen gets our offers fast (< 5 s, Ledger 40 s late)", first is not None and first < 5, f"{first} {to_cit}")
    check("copy: no 'no slot here', no partner search", "cross_asst" not in to_cit and "non ci sono posti" not in to_cit, to_cit)
    # No copy; the Ledger answers within the booking's patient wait (2 s of a 4 s budget here).
    first, to_cit, to_bc, asked = await run(copy=False, delay=2.0)
    check("no copy: hospital says ledger_slow, never no_availability", to_bc and all("no_availability" not in t for t in to_bc) and any("ledger_slow" in t for t in to_bc), str(to_bc))
    check("no copy: the Ledger's slot reaches the citizen", "offer offer_id=of-W9" in to_cit, to_cit)
    check("no copy: no partner search, no waiting list", "cross_asst" not in to_cit and "waiting_list=true" not in to_cit, to_cit)
    print("failures:", bad)
asyncio.run(main())
