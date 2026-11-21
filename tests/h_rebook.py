# Level 6 (fault.cancel), facility side: the city calls off one of our bookings ->
# cancel reason=facility_cancelled + up to 3 alternatives (same doctor first) in ONE message.
# Run: python -I tests/h_rebook.py hospital/agent hospital
import asyncio, sys
exec(open("tests/h_test.py", encoding="utf-8").read().split("async def main")[0])
fails = 0
def ok(cond, msg):
    global fails
    print(("OK  " if cond else "FAIL"), msg); fails += (not cond)
async def main(role):
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(1, "tue", "2026-11-03"), slot(2, "wed", "2026-11-03"), slot(3, "wed", "2026-11-04", doc="asst-x-h2"),
           slot(4, "thu", "2026-11-05"), slot(5, "fri", "2026-11-06")])
    await turn(c, PBC, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=N-77", role)
    await turn(c, PBC, "confirm offer_id=of-S2 slot_id=S2 citizen=citizen:other/5 consent_ref=cx-1 facility=agent:hosp prescription_number=rx-9 request_id=N-77", role)
    ok(any("booking.receipt" in t for to, t in c.out if to == PBC), "booked and receipt sent")
    print("F1 city notice -> cancel + alternatives to the booking centre")
    await turn(c, "city:director", "fault.cancel booking_id=H1 reason=facility_cancel", role)
    out = [t for to, t in c.out if to == PBC]
    msg = out[0] if out else ""
    ok(len(out) == 1, f"one message (got {len(out)})")
    ok(msg.startswith("cancel reason=facility_cancelled booking_id=H1") and "offer_id=of-S2" in msg.split("\n")[0], "cancel line names booking and offer")
    alts = A._offers_in(msg)
    ok(1 <= len(alts) <= 3 and all(o["slot_id"] != "S2" for o in alts), f"1-3 alternatives, not the lost slot ({[o['slot_id'] for o in alts]})")
    ok(all("request_id=N-77" in line for line in msg.split("\n") if line.startswith(("offer", "cancel"))), "request_id echoed")
    ok(alts and alts[0].get("doctor_id") == "asst-x-h1", "same doctor first")
    print("F2 same notice again -> nothing")
    await turn(c, "city:director", "fault.cancel booking_id=H1 reason=facility_cancel", role)
    ok(not [t for to, t in c.out if to == PBC], "idempotent")
    print("F3 notice for a booking that is not ours -> nothing sent")
    c2 = C([slot(1, "tue", "2026-11-03")])
    await turn(c2, "city:director", "fault.cancel booking_id=ZZ reason=facility_cancel", role)
    ok(not [t for to, t in c2.out if to != LEDGER], "unknown booking ignored")
    print("failures:", fails)
asyncio.run(main(sys.argv[2]))
