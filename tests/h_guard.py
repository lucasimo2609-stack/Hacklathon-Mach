"""Guards (21 Nov 15:09):
1. Clock: a citizen's reason=past on a slot DAYS ahead (they also use 'past' for a date they do
   not want) must not push the agent's clock forward; a plausible lag (a few hours) still does.
2. Message age: a sent_at far in the past or in the future (clock skew) is not 'old'.
3. Case reads: the long wait for a slow Ledger backs off (far fewer history reads).
Run: tests/h_guard.py hospital/agent hospital"""
import asyncio, sys, itertools, os, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from datetime import datetime, timedelta, timezone
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); ME = "agent:h6r1v45esk77"; BC = "agent:cdc7x6m21nj6"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
async def main(role):
    base = datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc)
    A._AGENDA_SEEN = (time.monotonic(), base); A._PAST_SEEN = None; A._PAST_REPORTS.clear()
    A._note_past(base + timedelta(days=3), "N-a")
    now = A._agenda_now()
    check("one citizen's 'past' 3 days ahead: clock unchanged", now < base + timedelta(hours=1), str(now))
    A._note_past(base + timedelta(days=3), "N-a")
    check("the same citizen again: still unchanged", A._agenda_now() < base + timedelta(hours=1), str(A._agenda_now()))
    A._note_past(base + timedelta(hours=30), "N-b")
    now = A._agenda_now()
    check("a second citizen confirms a big lag: clock moves to the nearer one (30 h)",
          base + timedelta(hours=29) < now < base + timedelta(hours=31), str(now))
    A._AGENDA_SEEN = (time.monotonic(), base); A._PAST_SEEN = None; A._PAST_REPORTS.clear()
    A._note_past(base + timedelta(hours=4))
    now = A._agenda_now()
    check("'past' on a slot 4 h ahead (plausible lag): clock moves there", now >= base + timedelta(hours=4), str(now))
    real = datetime.now(timezone.utc)
    def msg(dt): return Message(type="chat", sender=BC, msg_id="x", sent_at=dt.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
    check("age 12 min is read", 700 < (A._age(msg(real - timedelta(minutes=12))) or 0) < 740, "")
    check("age of a 2-day-old stamp is None (clock skew)", A._age(msg(real - timedelta(days=2))) is None, "")
    check("age of a stamp 1 h in the future is None", A._age(msg(real + timedelta(hours=1))) is None, "")
    # 3. reads during a patient wait with a silent Ledger (scaled budget: 15 s in this test)
    class C:
        def __init__(s): s.need = "N-g"; s.rows = []; s.reads = 0
        agent_id = property(lambda s: ME); address = ""
        async def history(s, peer=None, *, need_id=None):
            s.reads += 1; return list(s.rows)
    c = C(); A._INFLIGHT = 0
    t0 = time.monotonic()
    got = await A._await_patient(c, "N-g", [], "held", "slot_id=Z", op="hold")
    took = time.monotonic() - t0
    check("silent Ledger: the patient wait still ends (None)", got is None and took < 20, f"{took:.1f}s")
    check("silent Ledger: case reads back off (< 35 reads, was ~90)", c.reads < 35, str(c.reads))
    print(f"reads {c.reads} in {took:.1f}s")
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
