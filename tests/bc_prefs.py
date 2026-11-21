"""Citizen preferences in the FIRST offer list (21 Nov, journeys ...298 and ...225: the citizen
cancelled every offer -> -1 "no booking although acceptable slots were free").
 1. Named days are a hard filter: "solo di martedì o venerdì" never gets a Monday.
 2. Non-urgent slots must still be ahead when the offer is read (cancel reason "past").
 3. "Only certain days" without naming them: ask days and gender once, then offer to match.
Run: tests/bc_prefs.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:240]}")
# Monday 21 Dec 2026, 13:00 agenda. h1 f mon-wed, h2 m wed-fri, h3 m tue/thu.
WORLD = (" slot_id=MON15 doctor_id=asst-giambellino-h1 facility=hospital at=2026-12-21T15:00"
         " slot_id=MON17 doctor_id=asst-giambellino-h1 facility=hospital at=2026-12-21T17:00"
         " slot_id=TUE1 doctor_id=asst-giambellino-h1 facility=hospital at=2026-12-22T10:30"
         " slot_id=TUE3 doctor_id=asst-giambellino-h3 facility=hospital at=2026-12-22T10:30"
         " slot_id=WED2 doctor_id=asst-giambellino-h2 facility=hospital at=2026-12-23T09:00"
         " slot_id=FRI2 doctor_id=asst-giambellino-h2 facility=hospital at=2026-12-25T09:00")
class World(FakeCity):
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "prescription":
            s.add(LEDGER, BC, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=D state=issued")
        elif head == "agenda":
            s.add(LEDGER, BC, "agenda agenda_now=2026-12-21T13:00:00+00:00")
        elif head == "world":
            body = WORLD if f.get("procedure") == "VIS-FIS" else ""
            s.add(LEDGER, BC, f"world procedure={f.get('procedure')} page=1/1 slots={6 if body else 0}{body}")
def offered(c):
    sent = " ".join(t for to, t in c.out if to == CIT)
    return {sid for sid in ("MON15", "MON17", "TUE1", "TUE3", "WED2", "FRI2") if f"slot_id={sid}" in sent}, sent
async def main():
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = World(slots=[])
    await turn(c, CIT, "Vorrei un appuntamento per il ginocchio, ma solo di martedì o venerdì. prescription_number=rx-1 lang=it")
    got, sent = offered(c)
    check("named days: only Tuesday/Friday offered", got and got <= {"TUE1", "TUE3", "FRI2"}, f"{sorted(got)} {sent}")
    check("lead time: no slot at or before now + 2 h", "MON15" not in got, str(sorted(got)))
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = World(slots=[])
    await turn(c, CIT, "Gentili, vorrei una visita al ginocchio tenendo presente la mia disponibilità limitata ad alcuni giorni. prescription_number=rx-1 lang=it")
    got, sent = offered(c)
    check("vague days: asks days and gender before guessing", "fields=days,gender" in sent and not got, sent)
    await turn(c, CIT, "data.response days=tue gender=m")
    got, sent = offered(c)
    check("after the answer: Tuesday with a male doctor (h3) only", got == {"TUE3"}, f"{sorted(got)} {sent}")
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = World(slots=[])
    await turn(c, CIT, "Vorrei prenotare una visita. prescription_number=rx-1 lang=it")
    got, sent = offered(c)
    check("no stated limits: offers at once, no question", got and "fields=days" not in sent, sent)
    print("failures:", bad)
asyncio.run(main())
