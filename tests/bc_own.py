"""Booking centre <-> own hospital, directly. When the Ledger is slow to send the slot list,
the booking centre asks our hospital (need.request, source=own_asst); the hospital answers from
its own copy of its slots and the citizen gets offers in the same turn. Our hospital is never
treated as a partner ASST (no consent, no cross-ASST). Run: tests/bc_own.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
A._SLOW_WAIT = 12.0
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:220]}")
OUR_H = "agent:h6r1v45esk77"
class NoWorld(FakeCity):
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "prescription":
            s.add(LEDGER, BC, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=B state=issued")
        elif head == "agenda":
            s.add(LEDGER, BC, "agenda agenda_now=2026-11-16T08:00:00+00:00")
        # world: never answered (slow Ledger)
    async def say(s, to, text, status=None):
        r = await FakeCity.say(s, to, text, status)
        if to == OUR_H and text.startswith("need.request"):
            async def answer():
                await asyncio.sleep(0.5)
                s.add(OUR_H, BC, "Ricevuto, verifico subito la disponibilità per procedure=VIS-FIS.")
                s.add(OUR_H, BC, "offer offer_id=of-H1 slot_id=H1 doctor_id=asst-giambellino-h1 facility=agent:h6r1v45esk77 "
                                  "procedure=VIS-FIS agenda_date=2026-11-17T10:30:00+00:00 agenda_day=tue priority=B")
            asyncio.ensure_future(answer())
        return r
async def main():
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = NoWorld(slots=[])
    await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    to_h = [t for to, t in c.out if to == OUR_H]
    sent = " ".join(t for to, t in c.out if to == CIT)
    check("booking asked our own hospital directly", any(t.startswith("need.request") and "source=own_asst" in t for t in to_h), str(to_h))
    check("citizen offered the hospital's slot H1 in the same turn", "slot_id=H1" in sent, sent)
    check("no cross-ASST consent for our own hospital", "cross_asst" not in sent, sent)
    print("failures:", bad)
asyncio.run(main())
