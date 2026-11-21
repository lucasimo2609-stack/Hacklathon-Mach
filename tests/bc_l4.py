# Level 4 (scarcity) at the booking centre, from journeys of 20-21 Nov:
#  - 000172: ~11 s waiting for 8 pages of 10 slots it did not need (pages are date-sorted)
#  - 510002/530002/000172: waiting list 3-5 s after consent, partner slots came later
#  - 940006: a partner refused the hold -> bare cancel, the other partner slot never re-shown
# Run: $PY -I tests/bc_l4.py booking_centre/agent tests/bc_test.py
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, ("| " + info[:300]) if info and not ok else "")

def sl(i, date, hour, doc="asst-x-h1", day="mon"):
    return f"slot_id=Q{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={date}T{hour:02d}:30:00+00:00 day={day} free=1"

class Sorted(FakeCity):
    """8 pages, date-sorted from today; page 1 already runs past a priority-B deadline."""
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "world" and f.get("procedure") == "VIS-FIS":
            page = int(f.get("page", "1"))
            if page == 1:
                rows = [sl(1, "2026-11-02", 13), sl(2, "2026-11-03", 10, day="tue"), sl(3, "2026-11-05", 10, day="thu")]
            else:
                rows = [sl(10 * page, "2026-11-1%d" % page, 10, day="tue")]
            s.add(LEDGER, BC, f"slots from=2026-11-02 until=2026-11-30 matching=80 page={page}/8 procedure=VIS-FIS\n" + "\n".join(rows))
        elif head == "world":
            s.add(LEDGER, BC, f"slots page=1/1 procedure={f.get('procedure')}")
        else:
            super().ledger(text)

PA, PB = "agent:part-a", "agent:part-b"
def poff(slot, fac, hour=10):
    return (f"offer offer_id=po-{slot} slot_id={slot} doctor_id=asst-y-h1 facility={fac} procedure=VIS-FIS "
            f"agenda_date=2026-11-03T{hour:02d}:30:00+00:00 agenda_day=tue")

async def say(c, sender, text):
    m = c.add(sender, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    return [(to, t) for to, t in c.out if to == CIT]

async def main():
    A._PARTNER_SETTLE = 0.1; A._PARTNER_WAIT = 2.0; A._PARTNER_POLL = 0.05; A._AGENDA_SEEN = None
    # 1. Date-sorted pages: page 1 already passes the B deadline -> choose without more pages
    c = Sorted(slots=[])
    await say(c, CIT, "prenoto prescription_number=rx-1")
    pages = [t for to, t in c.out if to == LEDGER and t.startswith("world procedure=VIS-FIS")]
    offers = [o["slot_id"] for to, t in c.out if to == CIT for o in A._offers_in(t)]
    check("pages: no page beyond 1 asked when page 1 passes the deadline", all("page=1" in t for t in pages), str(pages))
    check("pages: offers from page 1", set(offers) == {"Q1", "Q2"}, str(offers))

    peers = [Peer(agent_id=x, role="facility", capabilities=("hospital.physiatry",)) for x in (PA, PB)]
    # 2. A partner answers 1 s after the consent: offers, not the waiting list
    c = FakeCity(slots=[], peers=peers)
    await say(c, CIT, "prenoto prescription_number=rx-1")
    async def late():
        await asyncio.sleep(0.8); c.add(PA, BC, poff("P1", PA))
        await asyncio.sleep(0.2); c.add(PB, BC, "cancel offer_id=none reason=no_availability")
    task = asyncio.create_task(late())
    out = await say(c, CIT, "consent consent_ref=cx-9 purpose=cross_asst")
    await task
    check("slow partner: its slot offered, no waiting list", any("slot_id=P1" in t for _, t in out) and not any("waiting_list=true" in t for _, t in out), str(out))
    check("fast reply: instant 'checking nearby ASSTs' line first", out and "ASST vicine" in out[0][1] and not A._offers_in(out[0][1]), str(out[:1]))
    check("fast reply: then ONE offer message", len([1 for _, t in out if A._offers_in(t)]) == 1, str(out))

    # 3. Partners silent: the waiting list after the wait, never stuck
    c = FakeCity(slots=[], peers=peers)
    await say(c, CIT, "prenoto prescription_number=rx-1")
    t0 = time.monotonic(); out = await say(c, CIT, "consent consent_ref=cx-9 purpose=cross_asst"); took = time.monotonic() - t0
    check("silent partners: waiting list after the wait", any("waiting_list=true" in t for _, t in out) and took >= 1.5, f"{took:.1f}s {out}")

    # 4. A partner refuses the hold of P1: cancel P1, show P2 again to the CITIZEN
    c = FakeCity(slots=[], peers=peers)
    await say(c, CIT, "prenoto prescription_number=rx-1")
    c.add(PA, BC, poff("P1", PA) + "\n" + poff("P2", PA, hour=12))
    out = await say(c, CIT, "consent consent_ref=cx-9 purpose=cross_asst")
    check("fast reply: no extra line when partner slots are already in hand", not any("ASST vicine" in t for _, t in out), str(out))
    await say(c, CIT, "confirm offer_id=po-P1 consent_ref=cons-b")
    m = c.add(PA, BC, "cancel offer_id=po-P1 reason=hold_refused ledger_code=SLOT_TAKEN")
    c.out.clear(); await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    to_cit = [t for to, t in c.out if to == CIT]
    again = [o["slot_id"] for t in to_cit for o in A._offers_in(t)]
    check("refusal: citizen told P1 is cancelled", any(t.startswith("cancel offer_id=po-P1") for t in to_cit), str(to_cit))
    check("refusal: P2 shown again, not P1", again == ["P2"], str(again))
    check("refusal: nothing sent back to the partner", not any(to == PA and A._offers_in(t) for to, t in c.out))
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
