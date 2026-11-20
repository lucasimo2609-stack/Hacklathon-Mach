# Cross-ASST offers (journeys 000119, 690005, 710003 of 20 Nov): partner answers went out as
# 3-4 separate offer messages, one with the same slot twice, and a partner's "no availability"
# (cancel offer_id=none) reached the citizen as a cancelled booking.
# Run: $PY -I tests/bc_cross.py booking_centre/agent tests/bc_test.py
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])

bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, info)

PA, PB, PC = "agent:part-a", "agent:part-b", "agent:part-c"
def poff(slot, fac, date="2026-11-03", hour=10):
    return (f"offer offer_id=po-{slot} slot_id={slot} doctor_id=asst-y-h1 facility={fac} procedure=VIS-FIS "
            f"agenda_date={date}T{hour:02d}:30:00+00:00 agenda_day=tue")

async def say(c, sender, text):
    m = c.add(sender, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    return [(to, t) for to, t in c.out if to == CIT]

async def main():
    A._PARTNER_SETTLE = 0.3; A._AGENDA_SEEN = None
    peers = [Peer(agent_id=x, role="facility", capabilities=("hospital.physiatry",)) for x in (PA, PB, PC)]
    c = FakeCity(slots=[], peers=peers)
    await say(c, CIT, "prenoto prescription_number=rx-1")
    # Partner A answers before the consent; partner B answers during the settle window.
    c.add(PA, BC, poff("P1", PA) + "\n" + poff("P2", PA, hour=12))
    async def late():
        await asyncio.sleep(0.1)
        c.add(PB, BC, poff("P3", PB, hour=14) + "\n" + poff("P1", PA))  # P1 again: a duplicate
    task = asyncio.create_task(late())
    out = await say(c, CIT, "consent consent_ref=cx-9 purpose=cross_asst")
    await task
    msgs = [t for _, t in out if A._offers_in(t)]
    slots = [o["slot_id"] for t in msgs for o in A._offers_in(t)]
    check("one message after consent", len(msgs) == 1, str(len(msgs)))
    check("partner A and late partner B both in it", {"P1", "P2", "P3"} <= set(slots), str(slots))
    check("no slot twice", len(slots) == len(set(slots)), str(slots))
    # Partner C answers later, and partner D says it has nothing.
    out = await say(c, PC, poff("P4", PC, hour=15))
    check("later partner offer while choice is open: no new message", not out, str(out)[:150])
    out = await say(c, PC, "cancel offer_id=none reason=no_availability procedure=VIS-FIS request_id=N-1")
    check("partner 'no availability' never reaches the citizen", not out, str(out)[:150])
    # The citizen declines everything: the remaining partner slot (P4) comes in a new message.
    for s in slots:
        out = await say(c, CIT, f"cancel offer_id=po-{s} reason=day")
    again = [o["slot_id"] for _, t in out for o in A._offers_in(t)]
    check("after all declined: the unseen partner slot is offered", again == ["P4"], str(again))
    # A real cancel of an offer the citizen holds is still passed on.
    out = await say(c, PC, "cancel offer_id=po-P4 reason=facility_cancelled")
    check("cancel of a held offer is passed on", any("cancel offer_id=po-P4" in t for _, t in out), str(out)[:150])
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
