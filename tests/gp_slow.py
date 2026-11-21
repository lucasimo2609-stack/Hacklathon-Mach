"""GP reply time when every city call is slow (loaded city). The citizen must get the
prescription after ~2 calls, not after the extras (live: 5-9 min replies on 21 Nov)."""
import asyncio, sys, time, itertools
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
DELAY = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
ids = itertools.count(1); GP = "agent:c32jyk0cyan7"; CIT = "citizen:t/1"
class Slow:
    def __init__(s): s.need = f"N-{next(ids)}"; s.rows = []; s.log = []; s.t0 = 0; s.inbound = None
    agent_id = property(lambda s: GP); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b); s.rows.append(m); return m
    async def say(s, to, text, status=None):
        await asyncio.sleep(DELAY); s.add(GP, to, text); s.log.append((round(time.monotonic() - s.t0, 1), to, text))
        if to == LEDGER and text.startswith("world"):
            s.add(LEDGER, GP, "world slots=1 slot_id=S1 doctor_id=asst-giambellino-h1 facility=hospital procedure=VIS-FIS at=2026-11-03T10:30")
        if to == LEDGER and text.startswith("agenda"):
            s.add(LEDGER, GP, "agenda agenda_now=2026-11-02T08:00:00+00:00")
        return "x"
    async def history(s, peer=None, *, need_id=None): await asyncio.sleep(DELAY); return list(s.rows)
    async def find(s, q): await asyncio.sleep(DELAY); return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
async def main():
    c = Slow(); m = c.add(CIT, GP, "Buongiorno, ho mal di schiena da settimane."); c.inbound = m; c.t0 = time.monotonic()
    await A.handle("gp", c, m, list(c.rows))
    first = next((t for t, to, x in c.log if to == CIT and x.startswith("prescription")), None)
    print(f"city call delay {DELAY}s -> prescription to citizen at {first}s; total turn {round(time.monotonic()-c.t0,1)}s; calls {len(c.log)}")
    for t, to, x in c.log: print(f"   {t:>5}s -> {'LEDGER' if to==LEDGER else to} | {x[:110]}")
    bad = first is None or first > 3 * DELAY + 0.5
    print("failures:", int(bad))
asyncio.run(main())
