import asyncio, sys, itertools, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); ME = "agent:hosp"; PBC = "agent:partner-bc"
def slot(i, day, date, fac=ME, doc="asst-x-h1", proc="VIS-FIS"):
    return f"slot_id=S{i} doctor_id={doc} facility={fac} procedure={proc} at={date}T10:30:00+00:00 day={day} free=1"
class C:
    def __init__(s, slots): s.need=f"N-{next(ids)}"; s.rows=[]; s.out=[]; s.slots=slots; s.inbound=None
    agent_id=property(lambda s: ME); address=""
    def add(s,a,b,t):
        m=Message(type="chat",sender=a,msg_id=f"m{next(ids)}",need_id=s.need,body={"text":t},recipient=b); s.rows.append(m); return m
    async def say(s,to,text,status=None):
        s.add(ME,to,text); s.out.append((to,text))
        if to==LEDGER:
            f=A.fields_of(text); h=text.split()[0]
            if h=="agenda": s.add(LEDGER,ME,"agenda agenda_now=2026-11-02T08:00:00+00:00")
            if h=="world": s.add(LEDGER,ME,"slots page=1/1\n"+"\n".join(s.slots))
            if h=="hold": s.add(LEDGER,ME,f"held hold_id=H1 slot_id={f['slot_id']}")
            if h=="commit": s.add(LEDGER,ME,f"committed booking_id={f['hold_id']} ledger_ref=L1 slot_id=S2")
    async def history(s,peer=None,*,need_id=None): return list(s.rows)
    async def find(s,q): return []
    async def llm(s,*a,**k): raise CapError("KEY_UNKNOWN","x")
async def turn(c,who,text,role):
    m=c.add(who,ME,text); c.inbound=m; c.out.clear()
    await A.handle(role,c,m,await c.history())
    for to,t in c.out: print("   ->",to,"|",t.replace("\n"," // ")[:300])
async def main(role):
    print("A: partner asks VIS-FIS B -> our own slots only, one message")
    c=C([slot(1,"tue","2026-11-03"), slot(2,"wed","2026-11-03"), slot(3,"wed","2026-11-04", fac="agent:other")])
    await turn(c,PBC,"need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=N-77 Richiesta",role)
    print("B: partner confirms -> hold, commit, receipt to partner")
    await turn(c,PBC,"confirm offer_id=of-S2 slot_id=S2 citizen=citizen:other/5 consent_ref=cx-1 facility=agent:hosp prescription_number=rx-9",role)
    print("C: nothing free -> cancel with reason")
    c=C([]); await turn(c,PBC,"need.request service_type=hospital.physiatry procedure=VIS-FIS priority=U request_id=N-78",role)
asyncio.run(main(sys.argv[2]))
