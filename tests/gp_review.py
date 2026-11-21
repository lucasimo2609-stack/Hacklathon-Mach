# GP review points (journeys of 20-21 Nov: collaboration 0/220, proactivity 0 in 204, domain 0
# in 97 - "generic", "does not acknowledge the person", "pushes the booking back"). The reviewer
# reads only the citizen's conversation, so the extra work is done AND said there.
# 21 Nov 12:00 speed: the earliest slot comes from the GP's slot copy (the waited look-up found
# a slot 0 times in 44 live replies: the Ledger answers minutes later). The copy is refreshed
# without waiting; the Ledger's answers are handled in main() without reading the case.
# Run: $PY -I tests/gp_review.py gp/agent
import asyncio, sys, itertools, time, os
os.environ["CITY_ROLE"] = "gp"
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01; A._PROTOCOL_ASKED = True
ids = itertools.count(1); GP = A._GP_AGENT; BC = A._BC_AGENT; CIT = "citizen:t/7"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, ("| " + info[:320]) if info and not ok else "")

WORLD = ("slots wave_id=W01QQQ asst=asst-giambellino from=2026-11-16 until=2026-11-30 matching=3 page=1/1 "
         "slot_id=W-h2-1 doctor_id=asst-giambellino-h2 facility=agent:h6r1v45esk77 procedure=VIS-FIS agenda_date=2026-11-16T10:30:00.000Z agenda_day=mon "
         "slot_id=W-h1-1 doctor_id=asst-giambellino-h1 facility=agent:h6r1v45esk77 procedure=VIS-FIS agenda_date=2026-11-16T12:00:00.000Z agenda_day=mon "
         "slot_id=W-h1-2 doctor_id=asst-giambellino-h1 facility=agent:h6r1v45esk77 procedure=VIS-FIS agenda_date=2026-11-17T09:00:00.000Z agenda_day=tue")
AGENDA = "agenda agenda_now=2026-11-16T08:00:00+00:00"

class G:
    """The GP's side of one case. The Ledger never answers inside the turn (live: minutes)."""
    def __init__(s):
        s.need = f"N-{next(ids)}"; s.rows = []; s.history_calls = 0; s.inbound = None
    agent_id = property(lambda s: GP); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None): s.add(GP, to, text)
    async def history(s, peer=None, *, need_id=None):
        s.history_calls += 1; return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
    def to(s, who): return [r.text for r in s.rows if r.sender == GP and r.recipient == who]

class NeedStub:
    summary = ""

async def gp(c, text):
    m = c.add(CIT, GP, text)
    t = time.monotonic(); await A.handle("gp", c, m, await c.history())
    rx = next((x for x in c.to(CIT) if x.startswith("prescription ")), "")
    return rx, time.monotonic() - t

async def echo(text):
    """A Ledger answer arriving later as its own turn, through main() like in the city."""
    c = G(); m = c.add(LEDGER, GP, text); c.inbound = m
    await A.main(NeedStub(), c)
    return c

def reset():
    A._WORLD_SEEN.clear(); A._GP_WORLD_ASKED.clear(); A._AGENDA_SEEN = None

async def main():
    reset()
    # 1. Cold copy: prescription at once, no slot line; the slot query goes out AFTER the reply
    c = G(); rx, took = await gp(c, "Buongiorno dottore, ho mal di schiena da settimane")
    check("tokens unchanged", rx.startswith("prescription prescription_number=") and "procedure=VIS-FIS priority=B" in rx, rx[:120])
    check("domain: acknowledges THIS citizen (symptom, how long)", "Mi dispiace per il suo mal di schiena di questi giorni" in rx, rx)
    check("collaboration: says the booking centre was told, with its id", "Avviso subito il centro prenotazioni (agent:cdc7x6m21nj6)" in rx, rx)
    order = [(r.recipient, r.text.split()[0]) for r in c.rows if r.sender == GP]
    i_cit = next(i for i, (to, _) in enumerate(order) if to == CIT)
    check("speed: Ledger write, citizen, then booking notice", order[i_cit + 1][0] == BC and order[0][1] == "prescribe", str(order))
    check("speed: slot query sent after the reply, never waited on", any(to == LEDGER and h == "world" for to, h in order[i_cit:]) and took < 0.5, f"{took:.2f}s {order}")
    check("cold copy: no slot line", "primo posto" not in rx)
    check("one message to the citizen", len(c.to(CIT)) == 1, str(c.to(CIT)))

    # 2. The Ledger's answers arrive later as their own turns: cached, no case read
    w = await echo(WORLD); a = await echo(AGENDA)
    check("echo turns: no history read (instant)", w.history_calls == 0 and a.history_calls == 0, f"{w.history_calls}/{a.history_calls}")
    check("echo turns: nothing sent", not w.to(CIT) and not [r for r in w.rows if r.sender == GP])
    check("echo turns: slot copy and clock kept", "VIS-FIS" in A._WORLD_SEEN and A._AGENDA_SEEN is not None)

    # 3. Next citizens: earliest suitable slot named in the SAME message, no new query
    c = G(); rx, took = await gp(c, "I'm writing for my mother, her back hurts a lot. She only speaks English.")
    check("English + caregiver acknowledged", "I am sorry about your back pain, for the person you care for" in rx, rx)
    check("English-speaking doctor chosen (h1, not h2), in the prescription message", "the first time that suits you is Monday 16 November at 12:00" in rx, rx)
    check("throttle: no new slot query within 2 min", not any(r.recipient == LEDGER and r.text.startswith("world procedure=") for r in c.rows))
    c = G(); rx, _ = await gp(c, "Buongiorno, ho mal di schiena da giorni")
    check("Italian: h2 skipped (no Mondays), h1 named", "il primo posto adatto a lei è lunedì 16 novembre ore 12:00" in rx, rx)
    c = G(); rx, _ = await gp(c, "Back pain. Too busy, quick.")
    check("curt: brief line + first time only", "Book at the booking centre with this number." in rx and "first time" in rx and "sorry" not in rx, rx)

    # 4. A stale copy is never quoted; a red flag never triggers a look-up
    proc_time, text = A._WORLD_SEEN["VIS-FIS"]; A._WORLD_SEEN["VIS-FIS"] = (proc_time - 601, text)
    c = G(); rx, _ = await gp(c, "ho mal di schiena")
    check("copy older than 10 min: no slot line", rx and "primo posto" not in rx, rx)
    reset()
    c = G(); await gp(c, "dolore al petto fortissimo")
    check("red flag untouched: escalation, no look-up", any(t.startswith("escalate.emergency") for t in c.to(CIT)) and not any(r.recipient == LEDGER and r.text.startswith("world") for r in c.rows))
    # 5. Echoes the GP must act on still read the case (renewal, own prescribe)
    c = G(); m = c.add(LEDGER, GP, "prescribed prescription_number=rx-1 state=issued"); c.inbound = m
    await A.main(NeedStub(), c)
    check("prescribed echo: still handled with the case", c.history_calls >= 1, str(c.history_calls))
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
