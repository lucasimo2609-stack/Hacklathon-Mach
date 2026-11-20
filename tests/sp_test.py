import asyncio, sys, itertools
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); SP="agent:spec"; CIT="citizen:t/9"
class C:
    def __init__(s): s.need=f"N-{next(ids)}"; s.rows=[]; s.out=[]; s.inbound=None
    agent_id=property(lambda s: SP); address=""
    def add(s,a,b,t):
        m=Message(type="chat",sender=a,msg_id=f"m{next(ids)}",need_id=s.need,body={"text":t},recipient=b); s.rows.append(m); return m
    async def say(s,to,text,status=None):
        s.add(SP,to,text); s.out.append((to,text))
        if to==LEDGER:
            f=A.fields_of(text); h=text.split()[0]
            if h=="checkin": s.add(LEDGER,SP,f"checked_in booking_id={f['booking_id']}")
            if h=="report": s.add(LEDGER,SP,f"reported booking_id={f['booking_id']}")
            if h=="prescribe": s.add(LEDGER,SP,f"prescribed prescription_number={f['prescription_number']}")
    async def history(s,peer=None,*,need_id=None): return list(s.rows)
    async def find(s,q): return []
    async def llm(s,*a,**k): raise CapError("KEY_UNKNOWN","x")
async def turn(c,who,text):
    m=c.add(who,SP,text); c.inbound=m; c.out.clear()
    await A.handle("specialist_care",c,m,await c.history())
    for to,t in c.out: print("   ->",to,"|",t[:230])
async def main():
    print("A: consent given"); c=C(); c.add("agent:bc",SP,"confirm offer_id=of-S3 slot_id=S3 citizen=citizen:t/9 consent_ref=cb procedure=VIS-CARD")
    await turn(c,CIT,"checkin booking_id=B1 ledger_ref=L1")
    await turn(c,CIT,"consent consent_ref=cr-77 purpose=report_sharing")
    print("B: consent refused"); c=C(); await turn(c,CIT,"checkin booking_id=B2 ledger_ref=L2"); await turn(c,CIT,"no, preferisco di no")
    print("C: control visit CTRL-CARD -> no new follow-up"); c=C(); c.add("agent:bc",SP,"confirm offer_id=x slot_id=S9 citizen=citizen:t/9 consent_ref=cb procedure=CTRL-CARD")
    await turn(c,CIT,"checkin booking_id=B3 ledger_ref=L3"); await turn(c,CIT,"consent consent_ref=cr-5 purpose=report_sharing")
asyncio.run(main())
