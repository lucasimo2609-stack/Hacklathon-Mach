# History load control: reads per slow-Ledger citizen, a 20-citizen burst, the global cap on
# concurrent downloads, and our own line always visible right after we say it.
# run: python -I tests/history_load.py booking_centre/agent tests/bc_test.py
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
BAD = 0
def check(ok, label):
    global BAD
    BAD += 0 if ok else 1
    print(("ok   " if ok else "BAD  ") + label)
class Counting(FakeCity):
    calls = 0; live = 0; peak = 0
    async def history(s, peer=None, *, need_id=None):
        Counting.calls += 1; Counting.live += 1
        Counting.peak = max(Counting.peak, Counting.live)
        try:
            await asyncio.sleep(0.05)
            return list(s.rows)
        finally:
            Counting.live -= 1
class SlowLedger(Counting):
    def ledger(s, text):
        async def later():
            await asyncio.sleep(8.0)
            FakeCity.ledger(s, text)
        asyncio.ensure_future(later())
async def gated_turn(c, sender, text):
    # like bc_test.turn, but the first read goes through the gate as main() does live
    m = c.add(sender, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await A._history(c, c.need))
def reset():
    Counting.calls = Counting.peak = 0
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear(); A._HISTORY_CACHE.clear()
async def run(cls, n):
    reset(); t = time.monotonic()
    cities = [cls(slots=own) for _ in range(n)]
    await asyncio.gather(*[gated_turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it") for c in cities])
    offered = sum(any(to == CIT and "offer" in t.lower() for to, t in c.out) for c in cities)
    return Counting.calls, Counting.peak, time.monotonic() - t, offered
async def main():
    calls, peak, secs, offered = await run(Counting, 1)
    check(calls <= 3 and offered == 1, f"fast Ledger: {calls} downloads, offers sent")
    calls, peak, secs, offered = await run(SlowLedger, 1)
    check(calls <= 18 and secs < 10 and offered == 1, f"slow Ledger: {calls} downloads (was 24), {secs:.1f}s, offers sent")
    calls, peak, secs, offered = await run(SlowLedger, 20)
    check(calls <= 360 and peak <= A._HISTORY_GATE and secs < 13 and offered == 20,
          f"burst of 20: {calls} downloads (was 480), peak {peak} at once (cap {A._HISTORY_GATE}), {secs:.1f}s, {offered}/20 offered")
    # our own line is never hidden by the reuse window
    reset(); c = Counting(slots=own); c.inbound = c.add(CIT, BC, "ciao")
    await A._history(c, c.need)
    await c.say(CIT, "riga nostra")
    rows = await A._history(c, c.need)
    check(any(r.text == "riga nostra" for r in rows), "our own line seen right after say")
    # two turns reading the same case at the same moment share one download
    reset(); before = Counting.calls
    await asyncio.gather(A._history(c, c.need), A._history(c, c.need), A._history(c, c.need))
    check(Counting.calls - before == 1, f"3 simultaneous reads of one case -> {Counting.calls - before} download")
    print("TOTAL BAD", BAD)
asyncio.run(main())
