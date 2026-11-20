import asyncio, sys, itertools, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01; A._PULL_TRIES = 20
ids = itertools.count(1); ME = "agent:hosp"; CIT = "citizen:t/7"
class C:
    def __init__(s, answer): s.need=f"N-{next(ids)}"; s.rows=[]; s.out=[]; s.answer=answer; s.inbound=None
    agent_id=property(lambda s: ME); address=""
    def add(s,a,b,t):
        m=Message(type="chat",sender=a,msg_id=f"m{next(ids)}",need_id=s.need,body={"text":t},recipient=b); s.rows.append(m); return m
    async def say(s,to,text,status=None):
        s.add(ME,to,text); s.out.append((to,text))
        if to==LEDGER and text.startswith("checkin") and s.answer:
            s.add(LEDGER,ME,s.answer.format(**A.fields_of(text)))
    async def history(s,peer=None,*,need_id=None): return list(s.rows)
    async def find(s,q): return []
    async def llm(s,*a,**k): raise CapError("KEY_UNKNOWN","x")
async def turn(c,*a):
    sender,text,role=(a if len(a)==3 else (CIT,)+tuple(a))
    m=c.add(sender,ME,text); c.inbound=m; c.out.clear()
    await A.handle(role,c,m,await c.history())
    if not c.out: print("   SILENT")
    for to,t in c.out: print("   ->","LEDGER " if to==LEDGER else "citizen", "|", t[:120])
async def main(role):
    print("a) checkin, Ledger answers 'checkin_ok'"); await turn(C("checkin_ok booking_id={booking_id}"),"checkin booking_id=B1 ledger_ref=L1",role)
    print("b) checkin, Ledger answer never seen -> still welcomed"); await turn(C(None),"checkin booking_id=B2",role)
    print("c) 'sono arrivata' with the booking in the case"); c=C("checked_in booking_id={booking_id}"); c.add(LEDGER,ME,"committed booking_id=B3 ledger_ref=L3 slot_id=S1"); await turn(c,"Buongiorno, sono arrivata!",role)
    print("d) 'sono arrivata' with no booking known -> ask booking_id"); await turn(C(None),"sono arrivata",role)
    print("e) refused check-in"); await turn(C("refused op=checkin code=BOOKING_UNKNOWN booking_id={booking_id}"),"checkin booking_id=B9",role)
    print("f) a question we have no branch for"); await turn(C(None),"scusi, dove si parcheggia?",role)
asyncio.run(main(sys.argv[2]))
