"""Slow Ledger (21 Nov: ~20 open journeys stalled on "registro lento", others ended on a
wrong "no slot in our ASST" -> -1). The Ledger answers after DELAY seconds; the booking centre
must keep the turn alive, tell the citizen once, then offer our own slots. Never claim "no
slot" before the Ledger answered. Run: tests/bc_slow.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
A._PULL_PAUSE = 0.1
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:220]}")
class SlowLedger(FakeCity):
    def ledger(s, text):
        async def later():
            await asyncio.sleep(s.delay)
            FakeCity.ledger(s, text)
        asyncio.ensure_future(later())
async def run(delay):
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = SlowLedger(slots=own); c.delay = delay
    t = time.monotonic(); await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    took = time.monotonic() - t
    to_cit = [x for to, x in c.out if to == CIT]
    return c, to_cit, took
async def main():
    c, msgs, took = await run(15.0)
    joined = " ".join(msgs)
    check("Ledger 15 s late: our own slots offered in the same turn", "offer offer_id=of-S" in joined, joined)
    check("Ledger 15 s late: one 'slow register' line, no 'mi riscriva'", joined.count("registro regionale") == 1 and "riscriva" not in joined, joined)
    check("Ledger 15 s late: no cross-ASST, no waiting list", "cross_asst" not in joined and "waiting_list" not in joined, joined)
    c, msgs, took = await run(80.0)
    joined = " ".join(msgs)
    check("Ledger silent 80 s: never claims 'no slot in our ASST'", "cross_asst" not in joined and "non ci sono posti" not in joined, joined)
    check("Ledger 80 s late: citizen told once, turn bounded (< 130 s)", joined.count("registro regionale") == 1 and took < 130, f"{took:.0f}s {joined}")
    check("Ledger 80 s late: offers still delivered in the same turn (patient wait 2 min)", "offer offer_id=of-S" in joined, joined)
    print("failures:", bad)
asyncio.run(main())
