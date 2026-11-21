# Failed journeys of 21 Nov 00:00-01:41 (level 4-5), booking centre side:
#  - ...187/...204 (lang=wo) ...151/...153/...172 (lang=de): S had 5 slots in the one ASST that
#    speaks the language; its partner answered late or never -> waiting list -> the citizen turned
#    it down -> "in a few seconds I will send the times" -> silence (-1, retried every 15 min)
#  - ...104/...166/...128/...165 (VIS-CARD, S=208): the partner refused the hold, nothing else
#    in hand -> bare cancel, then silence
# Run: $PY -I tests/bc_ring.py booking_centre/agent tests/bc_test.py
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, ("| " + info[:400]) if info and not ok else "")
FORL = "agent:aycbxayckhrd"   # asst-forlanini hospital (German h3), from the city map
PA = "agent:part-a"
def poff(slot, fac, doc="asst-forlanini-h3", hour=10, rid=""):
    return (f"offer offer_id=po-{slot} slot_id={slot} doctor_id={doc} facility={fac} procedure=VIS-FIS "
            f"agenda_date=2026-11-03T{hour:02d}:30:00 agenda_day=tue" + (f" request_id={rid}" if rid else ""))
async def say(c, sender, text):
    m = c.add(sender, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    return [(to, t) for to, t in c.out if to == CIT]
async def main():
    A._PARTNER_SETTLE = 0.1; A._PARTNER_WAIT = 1.0; A._RARE_WAIT = 3.0; A._PARTNER_POLL = 0.05; A._AGENDA_SEEN = None
    print("1 German speaker: Forlanini is asked first and waited for (answers after 2 s)")
    c = FakeCity(slots=[])
    await say(c, CIT, "my back hurts, I need a doctor who speaks my language prescription_number=rx-1 lang=de")
    asked = [to for to, t in c.out if t.startswith("need.request")]
    check("Forlanini's hospital asked first", asked and asked[0] == FORL, str(asked[:3]))
    check("every ring hospital asked", len(set(asked)) >= 20, str(len(set(asked))))
    async def late():
        await asyncio.sleep(2.0); c.add(FORL, BC, poff("F1", FORL))
    task = asyncio.create_task(late())
    out = await say(c, CIT, "data.response purpose=cross_asst"); await task
    check("German slot offered, no waiting list", any("slot_id=F1" in t for _, t in out) and not any("waiting_list=true" in t for _, t in out), str(out))

    print("2 waiting list turned down, a partner answers the second round -> offers")
    c = FakeCity(slots=[])
    await say(c, CIT, "prenoto prescription_number=rx-1 lang=de")
    out = await say(c, CIT, "data.response purpose=cross_asst")
    check("nothing in time -> waiting list", any("waiting_list=true" in t for _, t in out), str(out))
    async def late2():
        for _ in range(100):
            await asyncio.sleep(0.05)
            if any(r.sender == BC and "-r2" in r.text for r in c.rows):
                break
        await asyncio.sleep(0.2); c.add(FORL, BC, poff("F2", FORL, rid=c.need + "-r2"))
    task = asyncio.create_task(late2())
    out = await say(c, CIT, f"no thanks, I need a doctor who speaks my language cancel offer_id=wl-{c.need} reason=waiting_list"); await task
    check("second round sent", any(r.sender == BC and r.text.startswith("need.request") and "-r2" in r.text for r in c.rows), "")
    check("second-round slot offered", any("slot_id=F2" in t for _, t in out), str(out))

    print("3 waiting list turned down, nobody has anything -> one honest closing line, then waiting list on yes")
    c = FakeCity(slots=[])
    await say(c, CIT, "prenoto prescription_number=rx-1 lang=de")
    await say(c, CIT, "data.response purpose=cross_asst")
    out = await say(c, CIT, f"no thanks cancel offer_id=wl-{c.need} reason=waiting_list")
    check("closing line, no empty promise left hanging", any("due volte" in t or "twice" in t for _, t in out), str(out))
    out = await say(c, CIT, "ok sì, mi metta in lista")
    check("yes -> waiting list again", any("waiting_list=true" in t and "wl2-" in t for _, t in out), str(out))

    print("4 partner refuses the hold, nothing else in hand -> second round -> new offer")
    c = FakeCity(slots=[], peers=[Peer(agent_id=PA, role="facility", capabilities=("hospital.physiatry",))])
    await say(c, CIT, "prenoto prescription_number=rx-1")
    c.add(PA, BC, poff("P1", PA, doc="asst-y-h1"))
    await say(c, CIT, "consent consent_ref=cx-9 purpose=cross_asst")
    await say(c, CIT, "confirm offer_id=po-P1 consent_ref=cons-b")
    async def late3():
        for _ in range(100):
            await asyncio.sleep(0.05)
            if any(r.sender == BC and "-r2" in r.text for r in c.rows):
                break
        await asyncio.sleep(0.2); c.add(PA, BC, poff("P9", PA, doc="asst-y-h1", hour=12, rid=c.need + "-r2"))
    task = asyncio.create_task(late3())
    out = await say(c, PA, "cancel offer_id=po-P1 reason=hold_refused ledger_code=SLOT_TAKEN"); await task
    check("citizen told P1 is gone", any(t.startswith("cancel offer_id=po-P1") for _, t in out), str(out))
    check("new slot from the second round offered", any("slot_id=P9" in t for _, t in out), str(out))

    print("5 on the waiting list (not turned down), a fitting partner slot arrives late -> shown")
    c = FakeCity(slots=[])
    await say(c, CIT, "prenoto prescription_number=rx-1 lang=de")
    await say(c, CIT, "data.response purpose=cross_asst")
    out = await say(c, FORL, poff("F5", FORL))
    check("late German slot shown to the citizen", any("slot_id=F5" in t for _, t in out), str(out))
    print("failures:", bad)
    sys.exit(1 if bad else 0)
asyncio.run(main())
