"""GP turn time with a slow platform (each say takes 1 s, 21 Nov 14:40 city-wide queue). The
citizen's prescription goes out after the Ledger write; the three follow-ups (booking notice,
slot copy refresh, protocol table) go out together. Expect the whole turn in < 3.6 s (5 serial
says would take >= 5 s) and the prescription to the citizen within 2.5 s.
Run: tests/gp_turn_speed.py gp/agent"""
import asyncio, sys, itertools, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); ME = "agent:c32jyk0cyan7"; CIT = "citizen:t/1"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
class C:
    def __init__(s): s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.t0 = None
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        await asyncio.sleep(1.0)
        s.add(ME, to, text); s.out.append((time.monotonic() - s.t0, to, text)); return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
async def main():
    A._PROTOCOL_ASKED = False
    c = C(); m = c.add(CIT, ME, "Buongiorno, ho mal di schiena da qualche settimana.")
    c.t0 = time.monotonic(); await A.handle("gp", c, m, await c.history()); took = time.monotonic() - c.t0
    rx = next((t for t, to, x in c.out if to == CIT and x.startswith("prescription")), None)
    check("prescription to the citizen within 2.5 s", rx is not None and rx < 2.5, f"{rx} {[(round(t,1),to,x[:30]) for t,to,x in c.out]}")
    check("whole GP turn < 3.6 s with 1 s per say (was 6 s)", took < 3.6, f"{took:.1f}s {[(round(t,1),to,x[:30]) for t,to,x in c.out]}")
    check("booking centre told", any(to == "agent:cdc7x6m21nj6" for t, to, x in c.out), str(c.out))
    print(f"turn {took:.1f}s, says {len(c.out)}")
    print("failures:", bad)
asyncio.run(main())
