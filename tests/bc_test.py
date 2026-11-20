import asyncio, sys, itertools
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, Peer, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1)
BC = "agent:bc"; CIT = "citizen:t/1"; HOSP = "agent:hosp"; PART = "agent:partner-hosp"
def slot(i, day, date, doc="asst-x-h1", fac=HOSP, proc="VIS-FIS"):
    return f"slot_id=S{i} doctor_id={doc} facility={fac} procedure={proc} at={date}T10:30:00+00:00 day={day} free=1"
class FakeCity:
    def __init__(s, rx_state="issued", slots=(), peers=(), down=()):
        s.need=f"N-{next(ids)}"; s.rows=[]; s.rx_state=rx_state; s.slots=list(slots); s.peers=list(peers); s.down=set(down); s.inbound=None; s.out=[]
    agent_id = property(lambda s: BC); address = ""
    def add(s, sender, to, text):
        m = Message(type="chat", sender=sender, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": text}, recipient=to)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        to = to.agent_id if isinstance(to, Peer) else to
        if to in s.down: raise CapError("TARGET_NOT_VISIBLE", "down")
        s.add(BC, to, text); s.out.append((to, text))
        if to == LEDGER: s.ledger(text)
        return "x"
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "prescription":
            s.add(LEDGER, BC, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=B state={s.rx_state}")
        elif head == "agenda":
            s.add(LEDGER, BC, "agenda agenda_now=2026-11-02T08:00:00+00:00")
        elif head == "world":
            s.add(LEDGER, BC, "slots page=1/1\n" + "\n".join(s.slots))
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return s.peers
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
async def turn(c, sender, text):
    m = c.add(sender, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    for to, t in c.out:
        if to != LEDGER: print("   ->", to, "|", t.replace("\n", " // ")[:260])
own = [slot(1,"mon","2026-11-02"), slot(2,"tue","2026-11-03"), slot(3,"wed","2026-11-03"), slot(4,"wed","2026-11-03", doc="asst-x-h2")]
async def main():
    print("S1 own slots -> one message, 3 offers"); c = FakeCity(slots=own); await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    print("S2 days=wed preference first"); c = FakeCity(slots=own); await turn(c, CIT, "prenoto prescription_number=rx-1 days=wed")
    print("S3 expired prescription -> renewal"); c = FakeCity(rx_state="expired", slots=own); await turn(c, CIT, "prenoto prescription_number=rx-1")
    print("S3b renewed number comes back -> offers"); c.rx_state="issued"; await turn(c, CIT, "ecco la nuova prescription_number=rx-2")
    print("S4 no own slots, partner exists -> partner asked + consent"); p = Peer(agent_id=PART, role="facility", capabilities=("hospital.physiatry",))
    c = FakeCity(slots=[], peers=[p]); await turn(c, CIT, "prenoto prescription_number=rx-1")
    print("  partner offer arrives first (no consent yet) -> nothing"); await turn(c, PART, "offer offer_id=po-1 slot_id=P1 doctor_id=asst-y-h1 facility=agent:partner-hosp procedure=VIS-FIS agenda_date=2026-11-03T10:30:00+00:00 agenda_day=tue")
    print("  citizen consents -> forwarded with via"); await turn(c, CIT, "consent consent_ref=cx-9 purpose=cross_asst")
    print("  citizen confirms partner offer -> confirm to partner"); await turn(c, CIT, "confirm offer_id=po-1 consent_ref=cons-N-1-booking")
    print("S5 no own slots, partner, citizen refuses -> waiting list"); c = FakeCity(slots=[], peers=[p]); await turn(c, CIT, "prenoto prescription_number=rx-1"); await turn(c, CIT, "no, preferisco di no")
    print("S6 no own slots, no partner -> waiting list"); c = FakeCity(slots=[]); await turn(c, CIT, "prenoto prescription_number=rx-1")
    print("S7 hospital down at confirm -> cancel + alternative"); c = FakeCity(slots=own, peers=[p], down={HOSP}); await turn(c, CIT, "prenoto prescription_number=rx-1"); await turn(c, CIT, "confirm offer_id=of-S2 consent_ref=cons-N-1-booking")
    print("S8 facility cancel with PRESCRIPTION_EXPIRED -> renewal"); c = FakeCity(slots=own); await turn(c, CIT, "prenoto prescription_number=rx-1"); await turn(c, HOSP, "cancel offer_id=of-S2 reason=facility_cancelled code=PRESCRIPTION_EXPIRED")
    print("S9 no prescription number -> asks for it"); c = FakeCity(slots=own); await turn(c, CIT, "buongiorno vorrei prenotare")
asyncio.run(main())
