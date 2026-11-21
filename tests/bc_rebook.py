# Level 6 (fault.cancel): the booking is called off -> cancel + new offers in ONE message.
# Run: python -I tests/bc_rebook.py booking_centre/agent tests/bc_test.py
import asyncio, sys
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main")[0])
fails = 0
def ok(cond, msg):
    global fails
    print(("OK  " if cond else "FAIL"), msg); fails += (not cond)
def to_cit(c): return [t for to, t in c.out if to == CIT]
async def booked(c):
    await turn(c, CIT, "vorrei prenotare prescription_number=rx-1")
    first = to_cit(c)[-1]
    oid = A._offers_in(first)[0]["offer_id"]; sid = A._offers_in(first)[0]["slot_id"]
    await turn(c, CIT, f"confirm offer_id={oid} consent_ref=cons-1")
    await turn(c, HOSP, f"booking.receipt booking_id=B-1 ledger_ref=L-1 offer_id={oid} slot_id={sid}")
    ok(any("booking.receipt" in t for t in to_cit(c)), "receipt forwarded")
    return oid, sid
async def main():
    print("R1 facility (MACH-1.2) calls off the booking -> one message: cancel on top + new offers")
    c = FakeCity(slots=own); oid, sid = await booked(c)
    await turn(c, HOSP, f"cancel reason=facility_cancelled booking_id=B-1 offer_id={oid}\noffer offer_id=of-S4 slot_id=S4 doctor_id=asst-x-h2 facility={HOSP} procedure=VIS-FIS agenda_date=2026-11-03T10:30:00\nIl posto è saltato")
    out = to_cit(c)
    ok(len(out) == 1, f"one message to the citizen (got {len(out)})")
    msg = out[0] if out else ""
    ok(msg.startswith(f"cancel offer_id={oid}") and "reason=facility_cancelled" in msg, "cancel line on top")
    offers = A._offers_in(msg)
    ok(offers and all(o["slot_id"] != sid for o in offers), "new offers, never the called-off slot")
    ok("annullato" in msg, "plain Italian explanation")
    print("R2 the same notice again -> nothing more (idempotent)")
    await turn(c, HOSP, f"cancel reason=facility_cancelled booking_id=B-1 offer_id={oid}")
    ok(not to_cit(c), "no second message")
    print("R3 the city tells the booking centre directly (fault.cancel, booking_id only)")
    c = FakeCity(slots=own); oid, sid = await booked(c)
    await turn(c, "city:director", "fault.cancel booking_id=B-1 reason=facility_cancel")
    out = to_cit(c); msg = out[0] if out else ""
    ok(len(out) == 1 and msg.startswith(f"cancel offer_id={oid}") and A._offers_in(msg), "cancel + offers from a city notice")
    print("R4 the citizen says it in words")
    c = FakeCity(slots=own); oid, sid = await booked(c)
    await turn(c, CIT, "Mi hanno appena scritto che la struttura ha annullato il mio appuntamento, cosa faccio?")
    out = to_cit(c); msg = out[0] if out else ""
    ok(len(out) == 1 and "reason=facility_cancelled" in msg and A._offers_in(msg), "rebooked from the citizen's words")
    print("R5 a world reply mentioning cancelled slots after the receipt -> no rebook")
    c = FakeCity(slots=own); oid, sid = await booked(c)
    await turn(c, LEDGER, "world slots=1 slot_id=S9 state=cancelled")
    ok(not any("facility_cancelled" in t for t in to_cit(c)), "Ledger world line is not a notice")
    print("R6 citizen turns offers down BEFORE booking -> not a rebook")
    c = FakeCity(slots=own); await turn(c, CIT, "vorrei prenotare prescription_number=rx-1")
    await turn(c, CIT, "cancel offer_id=of-S1 reason=past")
    ok(not any("facility_cancelled" in t for t in to_cit(c)), "rejection is not a rebook")
    print("R7 nothing else free -> the citizen still hears it at once")
    c = FakeCity(slots=[slot(1, "mon", "2026-11-02")]); oid, sid = await booked(c)
    await turn(c, HOSP, f"cancel reason=facility_cancelled booking_id=B-1 offer_id={oid}")
    ok(any("reason=facility_cancelled" in t for t in to_cit(c)), "cancel told even with no new slot")
    print("failures:", fails)
asyncio.run(main())
