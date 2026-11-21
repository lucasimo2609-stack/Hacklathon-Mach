"""Holding line, then silence (21 Nov 11:00, ...165/...225/...298): the Ledger's slot list never
came within 45 s and its late answer opened no turn. Here the Ledger loses the first world
request; the booking centre must ask again and offer in the same turn.
Run: tests/bc_stall.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
A._PULL_PAUSE = 0.05
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:220]}")
T0 = time.monotonic()
class LossyLedger(FakeCity):
    def ledger(s, text):
        # Overloaded Ledger: slot-list requests made in the first 70 s are lost.
        if text.startswith("world") and time.monotonic() - T0 < 70:
            return
        FakeCity.ledger(s, text)
async def main():
    global T0
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear(); T0 = time.monotonic()
    c = LossyLedger(slots=own)
    t = time.monotonic(); await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it"); took = time.monotonic() - t
    sent = " ".join(x for to, x in c.out if to == CIT)
    check("lost slot list: booking asks again and offers in the same turn", "offer offer_id=of-S" in sent, sent)
    check("no holding line: the offers are the first message (one citizen turn)", sent.count("registro regionale") == 0 and "offer offer_id=" in sent, sent)
    check(f"turn bounded (took {took:.0f}s < 130s)", took < 130, f"{took:.0f}s")
    print("failures:", bad)
asyncio.run(main())
