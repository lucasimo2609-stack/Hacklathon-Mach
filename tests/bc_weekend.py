"""Weekend bug (journeys of 21 Nov, e.g. citizen 000344): the agenda has no Saturday/Sunday,
but priority windows were counted in calendar days. On Friday evening a B citizen lost every
Monday/Tuesday slot -> "no suitable slot" -> judge: "no booking although acceptable slots were
free" (-1). Run: tests/bc_weekend.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys
from datetime import datetime, timezone
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:200]}")
fri = datetime(2026, 11, 13, 20, 38, tzinfo=timezone.utc)
check("B from Friday 20:38 -> Tuesday 20:38", A._agenda_plus(fri, 2) == datetime(2026, 11, 17, 20, 38, tzinfo=timezone.utc), str(A._agenda_plus(fri, 2)))
check("D from Wednesday -> next Wednesday", A._agenda_plus(datetime(2026, 11, 11, 9, tzinfo=timezone.utc), 5).day == 18)
check("B from Monday -> Wednesday", A._agenda_plus(datetime(2026, 11, 16, 9, tzinfo=timezone.utc), 2).day == 18)
class Friday(FakeCity):
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "prescription":
            s.add(LEDGER, BC, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority={s.prio} state=issued")
        elif head == "agenda":
            s.add(LEDGER, BC, "agenda agenda_now=2026-11-13T20:38:00+00:00")
        elif head == "world":
            body = "" if f.get("procedure") != "VIS-FIS" else (
                " slot_id=M1 doctor_id=asst-giambellino-h1 facility=hospital at=2026-11-16T10:30 day=mon"
                " slot_id=T1 doctor_id=asst-giambellino-h1 facility=hospital at=2026-11-17T09:00 day=tue"
                " slot_id=W1 doctor_id=asst-giambellino-h1 facility=hospital at=2026-11-18T09:00 day=wed")
            s.add(LEDGER, BC, f"world procedure={f.get('procedure')} page=1/1 slots={3 if body else 0}{body}")
async def main():
    for prio, want, not_want in (("B", {"M1", "T1"}, {"W1"}), ("D", {"M1", "T1", "W1"}, set())):
        A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
        c = Friday(slots=[]); c.prio = prio
        await turn(c, CIT, "prenoto prescription_number=rx-1 lang=it")
        sent = " ".join(t for to, t in c.out if to == CIT)
        offered = {sid for sid in ("M1", "T1", "W1") if f"slot_id={sid}" in sent}
        check(f"{prio} on Friday evening: offers {sorted(want)} from our hospital", want <= offered and not (offered & not_want), sent[:200])
        check(f"{prio}: no 'no suitable slot' / cross-ASST", "purpose=cross_asst" not in sent and "waiting_list=true" not in sent, sent[:200])
    print("failures:", bad)
asyncio.run(main())
