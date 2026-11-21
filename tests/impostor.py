# Sat 10:00 impostors: an agent outside the ring (real-format id, not on the city map at 01:45)
# gets no slots, its confirm holds nothing, its offers never reach the citizen.
# Run: python -I tests/impostor.py hospital/agent hospital
import asyncio, sys
exec(open("tests/h_test.py", encoding="utf-8").read().split("async def main")[0])
fails = 0
def ok(cond, msg):
    global fails
    print(("OK  " if cond else "FAIL"), msg); fails += (not cond)
FAKE = "agent:zzzz9999zzzz"
REAL = "agent:x0vr9rbwpesr"  # Corvetto hospital... used as a ring booking centre stand-in
async def main(role):
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(1, "tue", "2026-11-03"), slot(2, "wed", "2026-11-03")])
    await turn(c, FAKE, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=X1", role)
    ok(not [t for to, t in c.out if to == FAKE], "impostor gets no slots")
    await turn(c, FAKE, "confirm offer_id=of-S1 slot_id=S1 citizen=citizen:x/1 consent_ref=c prescription_number=rx facility=agent:hosp", role)
    ok(not any(r.sender == ME and r.text.startswith("hold") for r in c.rows), "impostor confirm holds nothing")
    await turn(c, REAL, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=R1", role)
    ok(any("offer" in t for to, t in c.out if to == REAL), "a ring member still gets offers")
    ok(not A._ring_member(FAKE) and A._ring_member(REAL) and A._ring_member("agent:part-a"), "ring membership")
    ranked = A._rank_partner_offers([(FAKE, {"slot_id": "F", "agenda_date": "2026-11-03T09:00:00"}), (REAL, {"slot_id": "R", "agenda_date": "2026-11-03T10:00:00"})], "it")
    ok([s for s, _ in ranked] == [REAL], "impostor offers dropped before the citizen sees them")
    print("failures:", fails)
asyncio.run(main(sys.argv[2]))
