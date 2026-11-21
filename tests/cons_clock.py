"""Consultorio clock and speed (21 Nov W01QQQ: the consultorio waited 16-18 min on a slow Ledger,
then offered slots already behind the agenda; citizens cancelled all four as past).
1. A citizen's 'past' on one case moves the clock for every case: the next citizen never gets a
   slot at or before that time.
2. Ledger silent, a 20-min-old copy of the consultorio's own list: offers within seconds.
Run: tests/cons_clock.py family_counseling/agent family_counseling"""
import asyncio, sys, itertools, os, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from datetime import datetime, timedelta, timezone
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01; A._SLOW_WAIT = 3.0; A._SLOW_REASK = 2.0; A._SLOW_POLL = 0.05
ids = itertools.count(1); ME = "agent:bzs050xacs1m"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
def line(i, at):
    day = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[datetime.fromisoformat(at).weekday()]
    return f"slot_id=K{i} doctor_id=asst-giambellino-c1 facility={ME} procedure=CONS-GIN at={at}:00+00:00 day={day} free=1"
SLOTS = [line(1, "2026-11-03T10:30"), line(2, "2026-11-03T14:30"), line(3, "2026-11-04T10:30"),
         line(4, "2026-11-04T14:30"), line(5, "2026-11-05T10:30"), line(6, "2026-11-05T14:30")]
class C:
    def __init__(s, agenda, silent=False):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.agenda = agenda; s.silent = silent
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(ME, to, text); s.out.append((to, text))
        if to == LEDGER and not s.silent:
            h = text.split()[0]
            if h == "agenda": s.add(LEDGER, ME, f"agenda agenda_now={s.agenda}:00+00:00")
            if h == "world": s.add(LEDGER, ME, "slots page=1/1\n" + "\n".join(SLOTS))
        return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
def offered(c, cit):
    return [A.fields_of(l).get("slot_id") for to, t in c.out if to == cit for l in t.splitlines() if l.startswith("offer offer_id=of-")]
def reset():
    A._WORLD_SEEN.clear(); A._AGENDA_SEEN = None; A._PAST_SEEN = None; A._INFLIGHT = 0; A._PAST_REPORTS.clear()
    A._LEARNED_LEAD = timedelta(0); A._OFFER_NOW.clear(); A._DOWN.clear()
async def main(role):
    reset()
    # Case 1: the Ledger says Tue 08:00 (stale); the citizen calls K3 (Wed 10:30) past.
    c1 = C("2026-11-03T08:00"); cit1 = "citizen:a/1"
    await A.handle(role, c1, c1.add(cit1, ME, "vorrei prenotare una visita al consultorio"), await c1.history())
    first = offered(c1, cit1)
    check("case 1: offers sent", bool(first), str(c1.out))
    victim = next((o for o in first if o in ("K3", "K4")), first[-1] if first else "K3")
    victim_at = next(l for l in SLOTS if f"slot_id={victim} " in l)
    at = A._when(A.fields_of(victim_at)["at"])
    await A.handle(role, c1, c1.add(cit1, ME, f"Non posso. cancel offer_id=of-{victim} reason=past"), await c1.history())
    # A lag of a day needs a second, different citizen saying the same (one citizen may just
    # dislike the date): the next case does.
    c1b = C("2026-11-03T08:00"); cit1b = "citizen:a/1b"
    await A.handle(role, c1b, c1b.add(cit1b, ME, "vorrei una visita al consultorio"), await c1b.history())
    if f"of-{victim}" in " ".join(t for to, t in c1b.out if to == cit1b):
        await A.handle(role, c1b, c1b.add(cit1b, ME, f"No. cancel offer_id=of-{victim} reason=past"), await c1b.history())
    clock = A._agenda_now()
    check("two citizens' past cancels move this agent's clock to at least that slot", clock is not None and clock >= at, f"{clock} < {at}")
    # Case 2: a new citizen, the Ledger STILL reports the stale Tue 08:00.
    c2 = C("2026-11-03T08:00"); cit2 = "citizen:b/2"
    await A.handle(role, c2, c2.add(cit2, ME, "buongiorno, vorrei una visita al consultorio"), await c2.history())
    got = offered(c2, cit2)
    later = [o for o in got if A._when(A.fields_of(next(l for l in SLOTS if f"slot_id={o} " in l))["at"]) <= at]
    check("case 2 (new citizen): nothing at or before the slot called past", got and not later, f"{got} early={later}")
    # Case 3: Ledger silent; a 20-min-old copy of the list -> offers within seconds.
    reset()
    A._AGENDA_SEEN = (time.monotonic(), datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc))
    A._WORLD_SEEN["CONS-GIN"] = (time.monotonic() - 1200, "slots page=1/1\n" + "\n".join(SLOTS))
    c3 = C("2026-11-03T08:00", silent=True); cit3 = "citizen:c/3"
    t0 = time.monotonic()
    await A.handle(role, c3, c3.add(cit3, ME, "vorrei una visita al consultorio"), await c3.history())
    took = time.monotonic() - t0
    check("silent Ledger + copy: offers to the citizen", bool(offered(c3, cit3)), str(c3.out))
    check("silent Ledger + copy: within 2.5 s (no long wait)", took < 2.5, f"{took:.1f}s")
    check("silent Ledger + copy: no waiting list", not any("waiting_list=true" in t for to, t in c3.out), str(c3.out))
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
