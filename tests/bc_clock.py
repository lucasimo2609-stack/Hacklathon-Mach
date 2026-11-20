# Journeys of 20 Nov (000095, 000099, 730003: ~60 offers; 000091, 000093: "no slot" then a
# partner slot past the deadline). Causes: a predicted agenda clock days behind (the market ran
# faster than 60x) and a citizen's cancel answered by re-sending the same offers.
# Run: $PY -I tests/bc_clock.py booking_centre/agent tests/bc_test.py
import asyncio, sys, time
from datetime import datetime, timedelta, timezone
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])

bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, info)

def sl(i, date, hour, doc="asst-x-h1", day="mon"):
    return f"slot_id=T{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={date}T{hour:02d}:30:00+00:00 day={day} free=1"

def offers_to_citizen(c):
    return [A.fields_of(l) for to, t in c.out if to == CIT for l in t.split("\n") if l.startswith("offer ") and "slot_id=" in l]

async def say(c, text):
    m = c.add(CIT, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    return c.out[:]

async def main():
    # 1. Stale predicted clock: the process last saw 20 Oct; the Ledger says 2 Nov 08:00.
    A._AGENDA_SEEN = (time.monotonic(), datetime(2026, 10, 20, 8, tzinfo=timezone.utc))
    slots = [sl(1, "2026-10-21", 10, day="wed"), sl(2, "2026-11-02", 13), sl(3, "2026-11-03", 10, day="tue")]
    c = FakeCity(slots=slots)
    await say(c, "prenoto prescription_number=rx-1")
    asked = [t for to, t in c.out if to == LEDGER and t.startswith("agenda")]
    ids = [o["slot_id"] for o in offers_to_citizen(c)]
    check("stale clock: agenda asked for the case", bool(asked) or any(r.text == "agenda" for r in c.rows if r.recipient == LEDGER))
    check("stale clock: past slot (21 Oct) never offered", "T1" not in ids and ids, str(ids))

    # 2. Cancel loop: the citizen cancels every offer as past -> wait while some are open,
    #    then new later slots once; a declined slot is never offered again.
    A._AGENDA_SEEN = None
    many = [sl(i, "2026-11-02", 12 + i) for i in range(1, 6)] + \
           [sl(10 + i, "2026-11-03", 8 + i, day="tue") for i in range(1, 4)] + \
           [sl(20, "2026-11-03", 10, doc="asst-x-h3", day="tue")]
    # Later Tuesday slots: still bookable once the clock jumps to the latest "past" slot.
    many += [sl(30, "2026-11-03", 15, day="tue"), sl(31, "2026-11-03", 16, day="tue")]
    c = FakeCity(slots=many)
    await say(c, "prenoto prescription_number=rx-1")
    first = offers_to_citizen(c)
    check("loop: first batch sent", len(first) >= 3, str([o["slot_id"] for o in first]))
    replies = []
    for o in first:
        replies.append(await say(c, f"Non mi va bene. cancel offer_id={o['offer_id']} reason=past"))
    mid = [r for r in replies[:-1] if any(to == CIT for to, _ in r)]
    check("loop: silent while some offers are still open", not mid, str(mid)[:200])
    print("   last reply:", [(to, t[:150]) for to, t in replies[-1]])
    last = [A.fields_of(l) for to, t in replies[-1] if to == CIT for l in t.split("\n") if l.startswith("offer ")]
    declined = {o["slot_id"] for o in first}
    check("loop: new offers after all declined", bool(last), str([o.get("slot_id") for o in last]))
    check("loop: no declined slot offered again", not ({o.get("slot_id") for o in last} & declined))
    floor = max(A._when(o["agenda_date"]) for o in first)
    check("loop: new offers are after the 'past' slots",
          all(A._when(o["agenda_date"]) > floor for o in last if o.get("agenda_date")))
    # Keep cancelling: offer messages stay bounded, and nothing declined comes back.
    for _ in range(10):
        batch = A._latest_batch(c.rows, BC, CIT)
        for o in batch:
            await say(c, f"cancel offer_id={o['offer_id']} reason=past")
    sent = [r for r in c.rows if r.sender == BC and r.recipient == CIT and A._offers_in(r.text)]
    slot_ids = [o.get("slot_id") for r in sent for o in A._offers_in(r.text) if o.get("slot_id")]
    check("loop: offer messages bounded", len(sent) <= A._MAX_OFFER_MESSAGES, str(len(sent)))
    check("loop: every slot offered at most once", len(slot_ids) == len(set(slot_ids)), str(slot_ids))

    # 3. Partner slot 9 days away for priority B, case without its own agenda line: refused.
    A._AGENDA_SEEN = (time.monotonic(), datetime(2026, 11, 9, 8, tzinfo=timezone.utc))
    offer = {"slot_id": "P1", "doctor_id": "asst-y-h1", "agenda_date": "2026-11-18T12:00:00.000Z"}
    check("partner: slot past the B deadline refused", not A._fits_partner(offer, [], "B"))
    offer = {"slot_id": "P2", "doctor_id": "asst-y-h1", "agenda_date": "2026-11-10T12:00:00.000Z"}
    check("partner: slot inside the B window kept", A._fits_partner(offer, [], "B"))

    # 4. Clock speed is learned from two fresh Ledger readings 10+ s apart.
    A._AGENDA_SEEN = (time.monotonic() - 20, datetime(2026, 11, 2, 8, tzinfo=timezone.utc))
    row = Message(type="chat", sender=LEDGER, msg_id="a", need_id="n", body={"text": "agenda agenda_now=2026-11-02T08:40:00+00:00"}, recipient=BC)
    A._remember([row])
    check("rate: 40 agenda min in 20 s -> ~120x", 100 <= A._AGENDA_RATE <= 140, str(round(A._AGENDA_RATE)))
    A._AGENDA_RATE = 60.0
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
