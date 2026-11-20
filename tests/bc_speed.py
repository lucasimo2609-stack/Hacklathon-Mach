import asyncio, sys, time, itertools
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
ids = itertools.count(1); BC="agent:bc"; CIT="citizen:t/1"
SLOTS = "\n".join(f"slot_id=S{i} doctor_id=asst-x-h1 facility=agent:hosp procedure=VIS-FIS at=2026-11-0{3+i%2}T10:30:00+00:00 day={'tue' if i%2==0 else 'wed'} free=1" for i in range(1,5))
class C:
    def __init__(s, delay): s.delay=delay; s.need=f"N-{next(ids)}"; s.rows=[]; s.log=[]; s.t0=0; s.inbound=None
    agent_id=property(lambda s: BC); address=""
    def add(s,a,b,t):
        m=Message(type="chat",sender=a,msg_id=f"m{next(ids)}",need_id=s.need,body={"text":t},recipient=b); s.rows.append(m); return m
    async def say(s,to,text,status=None):
        s.add(BC,to,text); s.log.append((round(time.monotonic()-s.t0,2),to,text))
        if to==LEDGER:
            async def reply():
                await asyncio.sleep(s.delay); f=A.fields_of(text); h=text.split()[0]
                if h=="agenda": s.add(LEDGER,BC,"agenda agenda_now=2026-11-02T08:00:00+00:00")
                if h=="world": s.add(LEDGER,BC,"slots page=1/1\n"+SLOTS)
                if h=="prescription": s.add(LEDGER,BC,f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=B state=issued")
            asyncio.ensure_future(reply())
    async def history(s,peer=None,*,need_id=None): return list(s.rows)
    async def find(s,q): return []
    async def llm(s,*a,**k): raise CapError("KEY_UNKNOWN","x")
async def run(label):
    c=C(1.5); m=c.add(CIT,BC,"vorrei prenotare prescription_number=rx-1"); c.inbound=m; c.t0=time.monotonic()
    await A.handle("booking_centre",c,m,await c.history())
    first = next((t for t,to,x in c.log if to==CIT), None)
    print(f"{label}: offers to citizen at {first}s; ledger calls: {[x.split()[0] for t,to,x in c.log if to==LEDGER]}")
async def main():
    await run("citizen 1 (cold)"); await run("citizen 2 (2nd in a row)")
asyncio.run(main())
