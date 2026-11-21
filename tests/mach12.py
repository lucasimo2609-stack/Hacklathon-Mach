# MACH-1.2 (level 5): extended criteria and relaxed offers on the partner side.
# Run: python -I tests/mach12.py hospital/agent hospital
import asyncio, sys
exec(open("tests/h_test.py", encoding="utf-8").read().split("async def main")[0])
fails = 0
def ok(cond, msg):
    global fails
    print(("OK  " if cond else "FAIL"), msg); fails += (not cond)
async def main(role):
    # Slots on Wed only (h1, female). Partner wants days=tue -> relaxed=days.
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(1, "wed", "2026-11-04", doc="asst-giambellino-h1"), slot(2, "wed", "2026-11-04", doc="asst-giambellino-h2")])
    await turn(c, PBC, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D days=tue request_id=R1", role)
    text = [t for to, t in c.out if to == PBC][-1]
    ok(text.startswith("cancel reason=no_availability"), "no exact fit -> cancel first")
    ok("relaxed=days" in text and "request_id=R1" in text, "relaxed=days offers under the cancel")
    ok(text.count("offer ") <= 3, "at most 3 relaxed offers")
    # days=wed fits -> plain offers, no cancel, no relaxed
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(1, "wed", "2026-11-04", doc="asst-giambellino-h1")])
    await turn(c, PBC, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D days=wed request_id=R2", role)
    text = [t for to, t in c.out if to == PBC][-1]
    ok("relaxed" not in text and not text.startswith("cancel"), "exact fit -> plain offers")
    # gender f wanted, only h2 (m) -> relaxed=gender
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(2, "wed", "2026-11-04", doc="asst-giambellino-h2")])
    await turn(c, PBC, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D gender_preference=f request_id=R3", role)
    text = [t for to, t in c.out if to == PBC][-1]
    ok("relaxed=gender" in text, "relaxed=gender when only a male doctor is free")
    # nothing at all -> plain cancel
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([])
    await turn(c, PBC, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=D days=tue request_id=R4", role)
    text = [t for to, t in c.out if to == PBC][-1]
    ok("cancel reason=no_availability" in text and "offer " not in text, "no slots -> cancel only")
    print("failures:", fails)
asyncio.run(main(sys.argv[2]))
