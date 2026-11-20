import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
def sl(i, day, date, doc="asst-x-h1", extra=""):
    return f"slot_id=T{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={date}T{9+i%6}:30:00+00:00 day={day} free=1 {extra}"
async def main():
    print("F1 confirm without consent -> consent ask; consent reply -> booking proceeds")
    c = FakeCity(slots=own); await turn(c, CIT, "prenoto prescription_number=rx-1")
    await turn(c, CIT, "confirm offer_id=of-S2"); await turn(c, CIT, "consent consent_ref=cb-1 purpose=booking")
    print("F2 unknown offer -> options again"); c = FakeCity(slots=own); await turn(c, CIT, "prenoto prescription_number=rx-1"); await turn(c, CIT, "confirm offer_id=of-ZZZ consent_ref=cb-1")
    print("F2b plain words after offers -> options again"); await turn(c, CIT, "va bene quello di martedì")
    print("F3 reserved slots (reserve=U, riserva=urgente) never offered to priority B")
    c = FakeCity(slots=[sl(1,"tue","2026-11-03",extra="reserve=U"), sl(2,"tue","2026-11-03",extra="riserva=urgente"), sl(3,"wed","2026-11-04")]); await turn(c, CIT, "prenoto prescription_number=rx-1")
    print("F4 diverse: same doctor many slots + other doctors/days")
    c = FakeCity(slots=[sl(1,"tue","2026-11-03"), sl(2,"tue","2026-11-03"), sl(3,"tue","2026-11-03"), sl(4,"wed","2026-11-04",doc="asst-x-h2"), sl(5,"thu","2026-11-05",doc="asst-x-h3")]); await turn(c, CIT, "prenoto prescription_number=rx-1")
asyncio.run(main())
