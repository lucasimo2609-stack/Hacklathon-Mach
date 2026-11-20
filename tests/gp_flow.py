import asyncio, sys, itertools, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); GP="agent:gp"; CIT="citizen:t/3"
class C:
    def __init__(s): s.need=f"N-{next(ids)}"; s.rows=[]; s.out=[]; s.inbound=None
    agent_id=property(lambda s: GP); address=""
    def add(s,a,b,t):
        m=Message(type="chat",sender=a,msg_id=f"m{next(ids)}",need_id=s.need,body={"text":t},recipient=b); s.rows.append(m); return m
    async def say(s,to,text,status=None): s.add(GP,to,text); s.out.append((to,text))
    async def history(s,peer=None,*,need_id=None): return list(s.rows)
    async def find(s,q): return []
    async def llm(s,*a,**k): raise CapError("KEY_UNKNOWN","x")
async def turn(c,text):
    m=c.add(CIT,GP,text); c.inbound=m; c.out.clear(); t=time.monotonic()
    await A.handle("gp",c,m,await c.history())
    ms=round((time.monotonic()-t)*1000)
    if not c.out: print(f"   ({ms}ms) SILENT")
    for to,x in c.out: print(f"   ({ms}ms) ->", "LEDGER" if to==LEDGER else "citizen", "|", x[:120])
async def main():
    print("1 symptom, then thanks/question, then resend"); c=C()
    await turn(c,"ho mal di schiena da settimane"); await turn(c,"grazie, ma dove devo andare adesso?"); await turn(c,"ho mal di schiena da settimane")
    print("2 red flag, then follow-ups never get a prescription"); c=C()
    await turn(c,"dolore al petto fortissimo"); await turn(c,"ok ma il cuore batte forte, mi dà una ricetta?")
    print("3 unknown, then the citizen explains"); c=C()
    await turn(c,"buongiorno, non sto bene"); await turn(c,"mi fa male il ginocchio")
asyncio.run(main())
