# Booking speed and error handling (21 Nov 12:45):
#  - the opening Ledger questions (prescription, agenda, slot lists) go out in parallel
#  - a send whose connection never opened is retried once; an ambiguous one (read timeout after
#    sending) is never retried, so no hold/confirm can be doubled
# Run: $PY -I tests/bc_parallel.py booking_centre/agent tests/bc_test.py
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
import httpx, logging
A._SEND_RETRY_PAUSE = 0.01
logging.getLogger("care").setLevel(logging.CRITICAL)  # the injected errors are logged by design
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:260]}")

class SlowSends(FakeCity):
    """Every send to the Ledger takes 0.3 s (a loaded city)."""
    async def say(s, to, text, status=None):
        if to == LEDGER:
            s.started = getattr(s, "started", []) + [time.monotonic()]
            await asyncio.sleep(0.3)
        return await FakeCity.say(s, to, text, status)

class Flaky(FakeCity):
    def __init__(s, errors, **k):
        super().__init__(**k); s.errors = list(errors); s.calls = 0
    async def say(s, to, text, status=None):
        if to == CIT:
            s.calls += 1
            if s.errors:
                raise s.errors.pop(0)
        return await FakeCity.say(s, to, text, status)

async def main():
    A._AGENDA_SEEN = None
    c = SlowSends(slots=own)
    m = c.add(CIT, BC, "prenoto prescription_number=rx-1"); c.inbound = m; c.out.clear()
    t0 = time.monotonic()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    opening = [t for t in c.started if t - t0 < 0.25]
    check("parallel: the opening Ledger questions start together", len(opening) >= 3, f"{len(opening)} started in the first 0.25 s of {len(c.started)}")
    check("parallel: offers still reach the citizen", any(to == CIT and "offer offer_id=" in t for to, t in c.out), str(c.out)[:200])

    req = httpx.Request("POST", "https://relay.example/messages")
    c = Flaky([httpx.ConnectError("refused", request=req)], slots=own)
    ok = await A._say(c, CIT, "hello")
    check("connect error: retried once, delivered once", ok and c.calls == 2 and sum(1 for to, t in c.out if to == CIT) == 1, f"ok={ok} calls={c.calls}")
    c = Flaky([httpx.ConnectTimeout("slow", request=req)] * 2, slots=own)
    ok = await A._say(c, CIT, "hello")
    check("connect error twice: a clean False, no crash", ok is False and c.calls == 2, f"ok={ok} calls={c.calls}")
    c = Flaky([httpx.ReadTimeout("after send", request=req)], slots=own)
    try:
        await A._say(c, CIT, "hello"); raised = False
    except httpx.ReadTimeout:
        raised = True
    check("read timeout (maybe delivered): never retried", raised and c.calls == 1, f"raised={raised} calls={c.calls}")
    # ...and the turn's safety net still answers the citizen when such an error escapes
    c = Flaky([httpx.ReadTimeout("after send", request=req)], slots=own)
    m = c.add(CIT, BC, "prenoto prescription_number=rx-1"); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    check("escaped error: the citizen still gets a line", any(to == CIT for to, _ in c.out), str(c.out)[:200])
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
