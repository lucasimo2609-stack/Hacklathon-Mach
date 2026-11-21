"""Priority window from the need's birth (21 Nov, wave W01QQQ: citizens cancelled B offers two
days out with reason=deadline, because our window was counted from "now" and the city takes
minutes = agenda hours per message). Run: tests/bc_window.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
import datetime as _dt
def line(i, at, doc="asst-x-h1"):
    day = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[_dt.datetime.fromisoformat(at).weekday()]
    return f"slot_id=W{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={at}:00+00:00 day={day} free=1"
class Clock(FakeCity):
    def ledger(s, text):
        if text.split()[0] == "agenda":
            s.add(LEDGER, BC, f"agenda agenda_now={s.now}:00+00:00")
        else:
            FakeCity.ledger(s, text)
def fresh(born, now, slots):
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = Clock(slots=slots); c.now = now
    c.add(LEDGER, BC, f"agenda agenda_now={born}:00+00:00")  # first reading (care.notice prefetch)
    return c
def offered(c):
    return " ".join(t for to, t in c.out if to == CIT)
async def main():
    # Born Tue 08:00, now Wed 06:00 (22 agenda hours of slow city). B = 48 h from birth.
    slots = [line(1, "2026-11-04T10:30"), line(2, "2026-11-04T16:00"), line(3, "2026-11-05T10:30"), line(4, "2026-11-06T10:30")]
    c = fresh("2026-11-03T08:00", "2026-11-04T06:00", slots)
    await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    got = offered(c)
    check("B born Tue 08:00: Wed slots offered", "slot_id=W1" in got and "slot_id=W2" in got, got)
    check("B born Tue 08:00: Thu 10:30 (past 48 h from birth) never offered", "slot_id=W3" not in got and "slot_id=W4" not in got, got)
    # The citizen turns one down as too late: nothing at or after it again.
    await turn(c, CIT, "No, troppo tardi. cancel offer_id=of-W2 reason=deadline")
    got = offered(c)
    check("after reason=deadline on Wed 16:00: no slot at or after it", "slot_id=W2" not in got and "slot_id=W3" not in got, got)
    # Born Friday: 48 h lands on Sunday (no agenda) -> the working-day rule keeps Monday.
    slots = [line(5, "2026-11-09T10:30"), line(6, "2026-11-10T10:30")]
    c = fresh("2026-11-06T08:00", "2026-11-06T12:00", slots)
    await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    got = offered(c)
    check("B born Friday: Monday slot still offered (weekend has no agenda)", "slot_id=W5" in got, got)
    check("B born Friday: Tuesday 10:30 (past the working-day window from birth) not offered", "slot_id=W6" not in got, got)
    # No first reading yet in this case: behaviour as before (window from now).
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = Clock(slots=[line(7, "2026-11-04T10:30")]); c.now = "2026-11-03T08:00"
    await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    check("first reading in the same turn: Wed slot offered", "slot_id=W7" in offered(c), offered(c))
    print("failures:", bad)
asyncio.run(main())
