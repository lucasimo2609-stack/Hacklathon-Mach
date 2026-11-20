import asyncio, sys, time, itertools, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
ids = itertools.count(1)
class C:
    def __init__(s, me, delay): s.me=me; s.delay=delay; s.need=f"N-{next(ids)}"; s.rows=[]; s.log=[]; s.t0=0; s.inbound=None
    agent_id=property(lambda s: s.me); address=""
    def add(s,a,b,t):
        m=Message(type="chat",sender=a,msg_id=f"m{next(ids)}",need_id=s.need,body={"text":t},recipient=b); s.rows.append(m); return m
    async def say(s,to,text,status=None):
        s.add(s.me,to,text); s.log.append((round(time.monotonic()-s.t0,2),to,text))
        if to==LEDGER:
            async def reply():
                await asyncio.sleep(s.delay); f=A.fields_of(text); h=text.split()[0]
                if h=="agenda": s.add(LEDGER,s.me,"agenda agenda_now=2026-11-02T08:00:00+00:00")
                if h=="world": s.add(LEDGER,s.me,"slots page=1/1\nslot_id=S1 doctor_id=asst-x-h1 facility=agent:hosp procedure=VIS-FIS at=2026-11-03T10:30:00+00:00 day=tue free=1")
                if h=="prescription": s.add(LEDGER,s.me,f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=B state=issued")
                if h=="hold": s.add(LEDGER,s.me,f"held hold_id=H1 slot_id={f['slot_id']}")
                if h=="commit": s.add(LEDGER,s.me,"committed booking_id=H1 ledger_ref=L1 slot_id=S1")
            asyncio.ensure_future(reply())
    async def history(s,peer=None,*,need_id=None): return list(s.rows)
    async def find(s,q): return []
    async def llm(s,*a,**k): raise CapError("KEY_UNKNOWN","x")
async def turn(c,role,who,text):
    m=c.add(who,c.me,text); c.inbound=m; c.log.clear(); c.t0=time.monotonic()
    await A.handle(role,c,m,await c.history())
    for t,to,txt in c.log: print(f"   {t:>5}s ->", to, "|", txt.replace(chr(10),' // ')[:150])
async def main():
    print("Hospital, cold (Ledger answers in 1.5s): partner request"); c=C("agent:hosp",1.5)
    await turn(c,"hospital","agent:pbc","need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=R1")
    print("Hospital, warm cache: second partner request"); c2=C("agent:hosp",1.5)
    await turn(c2,"hospital","agent:pbc2","need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=R2")
    print("Hospital: partner confirm"); await turn(c,"hospital","agent:pbc","confirm offer_id=of-S1 slot_id=S1 citizen=citizen:o/1 consent_ref=cx facility=agent:hosp")
    print("GP: agent asks to verify a prescription"); g=C("agent:gp",1.0)
    await turn(g,"gp","agent:pbc","verifica prescription_number=rx-5")
asyncio.run(main())
