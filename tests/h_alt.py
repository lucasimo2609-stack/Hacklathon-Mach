import asyncio, sys, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = "hospital"
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main(role):")[0])
class R(C):
    async def say(s,to,text,status=None):
        s.add(ME,to,text); s.out.append((to,text))
        if to==LEDGER:
            f=A.fields_of(text); h=text.split()[0]
            if h=="agenda": s.add(LEDGER,ME,"agenda agenda_now=2026-11-02T08:00:00+00:00")
            if h=="world": s.add(LEDGER,ME,"world slots=3 slot_id=S1 doctor_id=asst-g-h1 facility=hospital procedure=VIS-FIS at=2026-11-03T10:30 slot_id=S2 doctor_id=asst-g-h1 facility=hospital procedure=VIS-FIS at=2026-11-03T12:00 slot_id=S3 doctor_id=asst-g-h3 facility=hospital procedure=VIS-FIS at=2026-11-04T09:00")
            if h=="hold": s.add(LEDGER,ME,f"refused op=hold code=NO_CAPACITY slot_id={f['slot_id']}")
async def main():
    A._AGENDA_SEEN=None; A._WORLD_SEEN.clear(); A._HELD.clear()
    A._OWN_FACILITIES["hospital"]=ME
    print("partner asks -> offers; confirm S1 -> hold refused -> cancel + alternatives without S1")
    c=R([]); await turn(c,"agent:pbc","need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=R7","hospital")
    await turn(c,"agent:pbc","confirm offer_id=of-S1 slot_id=S1 citizen=citizen:o/1 consent_ref=cx facility=agent:hosp","hospital")
    print("second partner asks -> S1 (just held) not offered")
    c2=R([]); await turn(c2,"agent:pbc2","need.request procedure=VIS-FIS priority=B request_id=R8","hospital")
asyncio.run(main())
