# Level 7 (MACH-1.2 idempotency), facility side: duplicate need.request -> same offers;
# a partner's second round (new request_id) -> answered; duplicate confirm -> same receipt.
# Run: python -I tests/h_l7.py hospital/agent hospital
import asyncio, sys
exec(open("tests/h_test.py", encoding="utf-8").read().split("async def main")[0])
fails = 0
def ok(cond, msg):
    global fails
    print(("OK  " if cond else "FAIL"), msg); fails += (not cond)
async def main(role):
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(1, "tue", "2026-11-03"), slot(2, "wed", "2026-11-03")])
    req = "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=R-9"
    await turn(c, PBC, req, role)
    first = [t for to, t in c.out if to == PBC and "offer" in t][-1]
    await turn(c, PBC, req, role)
    again = [t for to, t in c.out if to == PBC]
    ok(again == [first], f"duplicate request -> the same offers ({len(again)})")
    await turn(c, PBC, req.replace("R-9", "R-9-r2"), role)
    r2 = [t for to, t in c.out if to == PBC]
    ok(r2 and ("request_id=R-9-r2" in r2[-1]), "second round (new request_id) answered")
    conf = "confirm offer_id=of-S2 slot_id=S2 citizen=citizen:other/5 consent_ref=cx-1 facility=agent:hosp prescription_number=rx-9 request_id=R-9"
    await turn(c, PBC, conf, role)
    receipt = [t for to, t in c.out if to == PBC and "booking.receipt" in t]
    holds1 = sum(1 for r in c.rows if r.sender == ME and r.text.startswith("hold"))
    await turn(c, PBC, conf, role)
    dup = [t for to, t in c.out if to == PBC]
    holds2 = sum(1 for r in c.rows if r.sender == ME and r.text.startswith("hold"))
    ok(receipt and dup == receipt, "duplicate confirm -> the same receipt")
    ok(holds1 == holds2 == 1, f"never a second hold ({holds1}->{holds2})")
    print("failures:", fails)
asyncio.run(main(sys.argv[2]))
