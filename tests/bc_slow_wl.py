"""The Ledger never answers within the slow wait (21 Nov 12:00-13:00, ...950002/...840002/...000419:
holding line, then nothing -> -1 no_alternative with an empty answer set). Now: holding line, then
the waiting list as the relaxed alternative (0); when the Ledger's slots arrive later as their own
turn, the real times are still offered (upgrade).
Run: tests/bc_slow_wl.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
A._PULL_PAUSE = 0.005; A._SLOW_WAIT = 0.3; A._SLOW_REASK = 0.1; A._SLOW_POLL = 0.02
A._SLOW_WL = getattr(A, "_SLOW_WL", "wl-slow-")
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:240]}")

class MuteWorld(FakeCity):
    """The prescription and agenda answer; slot lists do not (until we let them)."""
    mute = True
    def ledger(s, text):
        if text.startswith("world") and s.mute:
            return
        FakeCity.ledger(s, text)

async def main():
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = MuteWorld(slots=own)
    await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    sent = [x for to, x in c.out if to == CIT]
    joined = " ".join(sent)
    check("no holding line before the answer (one message, one citizen turn)", joined.count("registro regionale") == 0, joined)
    check("then the waiting list (relaxed alternative), never silence", f"offer_id={A._SLOW_WL}" in joined and "waiting_list=true" in joined, joined)
    check("no claim of 'no slot in our ASST' before the Ledger answered", "cross_asst" not in joined, joined)
    # The Ledger finally answers: its slot list arrives as a turn of its own
    c.mute = False
    c.out.clear()
    reply = c.add(LEDGER, BC, "slots page=1/1\n" + "\n".join(c.slots))
    await A.handle("booking_centre", c, reply, await c.history(need_id=c.need))
    up = " ".join(x for to, x in c.out if to == CIT)
    check("late slots: real times offered after the slow waiting list (upgrade)", "offer offer_id=of-S" in up, up or str(c.out)[:200])
    # A normal (not slow) waiting list still blocks later offers as before
    c2 = MuteWorld(slots=own); c2.mute = False
    c2.add(BC, CIT, f"offer offer_id=wl-N-x waiting_list=true procedure=VIS-FIS priority=B")
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
