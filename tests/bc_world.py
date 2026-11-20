import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
class RealShape(FakeCity):
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "prescription":
            s.add(LEDGER, BC, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=B state=issued")
        elif head == "agenda":
            s.add(LEDGER, BC, "agenda now=2026-11-02T08:00")
        elif head == "world":
            p = f.get("procedure")
            body = "" if p != "VIS-FIS" else (" slot_id=G1 doctor_id=asst-giambellino-h1 facility=hospital at=2026-11-03T10:30 posti=1"
                    " slot_id=G2 doctor_id=asst-giambellino-h3 facility=hospital at=2026-11-03T12:00 posti=1"
                    " slot_id=G3 doctor_id=asst-giambellino-h2 facility=hospital at=2026-11-04T09:00 posti=1 reserve=U")
            s.add(LEDGER, BC, f"world procedure={p} page=1/1 slots={3 if body else 0}{body}")
async def main():
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    print("real-shape world -> offers, reserved G3 skipped"); c = RealShape(slots=[]); await turn(c, CIT, "prenoto prescription_number=rx-1 lang=it")
    print("confirm -> goes to our hospital agent id"); await turn(c, CIT, "confirm offer_id=of-G1 consent_ref=cons-x-booking")
    print("cross: unclear answer -> asked again, then yes -> waits for partner")
    p = Peer(agent_id=PART, role="facility", capabilities=("hospital.physiatry",))
    c2 = FakeCity(slots=[], peers=[p]); await turn(c2, CIT, "prenoto prescription_number=rx-1"); await turn(c2, CIT, "Which consent_ref?")
    await turn(c2, PART, "offer offer_id=po-1 slot_id=P1 doctor_id=asst-y-h1 facility=agent:partner-hosp procedure=VIS-FIS agenda_date=2026-11-03T10:30:00+00:00 agenda_day=tue")
    await turn(c2, CIT, "sì, va bene")
asyncio.run(main())
