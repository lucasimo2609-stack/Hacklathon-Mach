# Specialist report flow, from live journeys of 20 Nov: citizens stayed silent after a bare
# "consent purpose=report_sharing" (000098/000103/000104: report_missing -1) or asked "Which
# consent_ref?" (980002: filed unshared, 0); every checkin/consent line went out twice.
# Turns run concurrently, as in the city. Run: $PY -I tests/sp_flow.py specialist/agent
import asyncio, sys, itertools
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01; A._REPORT_POLL = 0.05; A._REPORT_WAIT = 1.0
ids = itertools.count(1); SP = "agent:hnpe58epeyh1"; CIT = "citizen:t/9"; GP = A._GP_AGENT
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, info)

class C:
    def __init__(s, procedure="VIS-CARD"):
        s.need = f"N-{next(ids)}"; s.rows = []; s.inbound = None
        s.add("agent:cdc7x6m21nj6", SP, f"confirm offer_id=of-S3 slot_id=S3 citizen={CIT} consent_ref=cb procedure={procedure}")
    agent_id = property(lambda s: SP); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(SP, to, text)
        if to == LEDGER:
            f = A.fields_of(text); h = text.split()[0]
            if h == "checkin": s.add(LEDGER, SP, f"checked_in booking_id={f['booking_id']}")
            if h == "report": s.add(LEDGER, SP, f"reported booking_id={f['booking_id']}")
            if h == "prescribe": s.add(LEDGER, SP, f"prescribed prescription_number={f['prescription_number']}")
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
    def sent(s, to, head=None):
        return [r.text for r in s.rows if r.sender == SP and r.recipient == to and (head is None or r.text.split()[0] == head)]

async def turn(c, who, text):
    m = c.add(who, SP, text)
    await A.handle("specialist_care", c, m, await c.history())

async def visit(c, booking, answers, delay=0.2):
    """The citizen checks in; the Ledger's checked_in opens a second, parallel turn; the
    citizen's answers follow while the checkin turn is still waiting."""
    t1 = asyncio.create_task(turn(c, CIT, f"Sono arrivato. checkin booking_id={booking} ledger_ref=L1"))
    await asyncio.sleep(0.02)
    t2 = asyncio.create_task(turn(c, LEDGER, f"checked_in booking_id={booking}"))
    for text in answers:
        await asyncio.sleep(delay)
        await turn(c, CIT, text)
    await asyncio.gather(t1, t2)

def report_line(c):
    lines = c.sent(LEDGER, "report")
    return A.fields_of(lines[0]) if len(lines) == 1 else {"count": len(lines)}

async def main():
    # 1. Plain yes: shared with the consent_ref we named; follow-up prescribed; GP told.
    c = C(); await visit(c, "B1", ["sì, va bene"])
    asks = c.sent(CIT, "data.request")
    check("ask is a data.request naming its consent_ref", len(asks) == 1 and "consent_ref=" in asks[0], str(asks)[:160])
    check("one welcome, not two", len(c.sent(CIT, "checkin")) == 1, str(len(c.sent(CIT, "checkin"))))
    r = report_line(c)
    check("yes -> report shared with consent_ref", r.get("consent_ref", "").endswith("report_sharing"), str(r))
    check("first visit -> CTRL-CARD follow-up prescribed", len(c.sent(LEDGER, "prescribe")) == 1 and "follow_up_of=B1" in c.sent(LEDGER, "prescribe")[0])
    check("citizen gets report + follow-up prescription", len(c.sent(CIT, "report")) == 1 and len(c.sent(CIT, "prescription")) == 1)
    gp = c.sent(GP)
    check("GP gets one care.update with the follow-up", len(gp) == 1 and "follow_up_of=B1" in gp[0] and "care.update" in gp[0], str(gp)[:160])

    # 2. The citizen's own consent_ref is used as given.
    c = C(); await visit(c, "B2", ["consent consent_ref=cr-77 purpose=report_sharing"])
    check("given consent_ref kept", report_line(c).get("consent_ref") == "cr-77", str(report_line(c)))

    # 3. data.response without a ref (what citizens send for cross_asst) counts as yes.
    c = C(); await visit(c, "B3", ["data.response purpose=report_sharing"])
    check("data.response -> shared", "consent_ref" in report_line(c), str(report_line(c)))

    # 4. "Which consent_ref?" -> asked once more plainly; then yes -> shared.
    c = C(); await visit(c, "B4", ["Which consent_ref?", "sì"])
    check("unclear -> asked again once", len(c.sent(CIT, "data.request")) == 2)
    check("then yes -> shared", "consent_ref" in report_line(c), str(report_line(c)))

    # 5. Silence (000104): the report is filed unshared after the wait, never missing.
    c = C(); await visit(c, "B5", [])
    r = report_line(c)
    check("silence -> report still filed, unshared", r.get("shared") == "false", str(r))
    check("silence -> GP not told (no consent)", not c.sent(GP))
    check("silence -> citizen told it is kept, can ask for it", any("archiviato" in t for t in c.sent(CIT, "report")))

    # 6. A clear no: unshared, at once.
    c = C(); await visit(c, "B6", ["no, preferisco di no"])
    check("no -> unshared", report_line(c).get("shared") == "false", str(report_line(c)))

    # 7. A control visit (CTRL-CARD) gets no new follow-up.
    c = C("CTRL-CARD"); await visit(c, "B7", ["sì"])
    check("control visit -> no follow-up", not c.sent(LEDGER, "prescribe") and "consent_ref" in report_line(c))

    # 8. The GP's answer to our note is not a partner request (it carries procedure=).
    c = C(); m = c.add(GP, SP, "Verifica: prescription_number=rx-F1 procedure=CTRL-CARD priority=D state=issued")
    await A.handle("specialist_care", c, m, await c.history())
    check("GP reply ignored, no slots sent back", not c.sent(GP) and not c.sent(LEDGER))
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
