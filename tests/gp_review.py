# GP review points (journeys of 20-21 Nov: collaboration 0/220, proactivity 0 in 204, domain 0
# in 97 - "generic", "does not acknowledge the person", "pushes the booking back"). The reviewer
# reads only the citizen's conversation, so the extra work is done AND said there.
# Run: $PY -I tests/gp_review.py gp/agent
import asyncio, sys, itertools, time
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

WORLD = ("world slots=3 from=2026-11-16 page=1/2 procedure=VIS-FIS "
         "slot_id=W-h2-1 doctor_id=asst-giambellino-h2 facility=agent:h6r1v45esk77 procedure=VIS-FIS agenda_date=2026-11-16T10:30:00.000Z agenda_day=mon "
         "slot_id=W-h1-1 doctor_id=asst-giambellino-h1 facility=agent:h6r1v45esk77 procedure=VIS-FIS agenda_date=2026-11-16T12:00:00.000Z agenda_day=mon "
         "slot_id=W-h1-2 doctor_id=asst-giambellino-h1 facility=agent:h6r1v45esk77 procedure=VIS-FIS agenda_date=2026-11-17T09:00:00.000Z agenda_day=tue")

class G:
    def __init__(s, ledger=True):
        s.need = f"N-{next(ids)}"; s.rows = []; s.ledger = ledger
    agent_id = property(lambda s: GP); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(GP, to, text)
        if to == LEDGER and s.ledger:
            if text.startswith("world procedure="):
                s.add(LEDGER, GP, WORLD)
            elif text == "agenda":
                s.add(LEDGER, GP, "agenda agenda_now=2026-11-16T08:00:00+00:00")
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")

async def gp(c, text):
    m = c.add(CIT, GP, text)
    t = time.monotonic(); await A.handle("gp", c, m, await c.history())
    rx = next((r.text for r in c.rows if r.sender == GP and r.recipient == CIT and r.text.startswith("prescription ")), "")
    return rx, time.monotonic() - t

async def main():
    A._AGENDA_SEEN = None
    c = G(); rx, took = await gp(c, "Buongiorno dottore, ho mal di schiena da settimane")
    check("tokens unchanged", rx.startswith("prescription prescription_number=") and "procedure=VIS-FIS priority=B" in rx, rx[:120])
    check("domain: acknowledges THIS citizen (symptom, how long)", "Mi dispiace per il suo mal di schiena di questi giorni" in rx, rx)
    check("collaboration: says the booking centre was told, with its id", "Ho già avvisato il centro prenotazioni (agent:cdc7x6m21nj6)" in rx, rx)
    order = [r.recipient for r in c.rows if r.sender == GP]
    check("collaboration: the notice really went out BEFORE the reply", order.index(BC) < order.index(CIT), str(order))
    check("proactivity: earliest suitable slot named (h2 does not work Mondays)", "il primo posto adatto a lei è lunedì 16 novembre ore 12:00" in rx, rx)
    check("fast: reply within 2 s", took < 2.0, f"{took:.2f}s")

    A._AGENDA_SEEN = None
    c = G(); rx, _ = await gp(c, "I'm writing for my mother, her back hurts a lot. She only speaks English.")
    check("English + caregiver acknowledged", "I am sorry about your back pain, for the person you care for" in rx, rx)
    check("English-speaking doctor chosen (h1, not h2)", "the first time that suits you is Monday 16 November at 12:00" in rx, rx)

    A._AGENDA_SEEN = None
    c = G(ledger=False); rx, took = await gp(c, "ho male al ginocchio")
    check("Ledger silent: reply still goes out, no slot line", rx and "primo posto" not in rx and "Mi dispiace per il dolore al ginocchio" in rx, rx)
    check("Ledger silent: lookup capped (< 2 s)", took < 2.0, f"{took:.2f}s")

    A._AGENDA_SEEN = None
    c = G(); rx, _ = await gp(c, "Back pain. Too busy, quick.")
    check("curt: brief line + first time only", rx.count(".") <= 4 and "Book at the booking centre with this number." in rx and "first time" in rx and "sorry" not in rx, rx)

    A._AGENDA_SEEN = None
    c = G(); rx, _ = await gp(c, "dolore al petto fortissimo")
    check("red flag untouched: escalation, no lookup", any(r.text.startswith("escalate.emergency") for r in c.rows if r.sender == GP) and not any(r.recipient == LEDGER and r.text.startswith("world") for r in c.rows))
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
