# 21 Nov ...550007 (L6, answer set empty): after the cross-ASST consent the partners stayed
# silent, the citizen wrote again, and got "registro lento... mi riscriva" three times, never an
# alternative -> -1 no_alternative.
#  - nothing offered after the consent -> the next citizen message gets the waiting list (0)
#  - already on the waiting list -> an honest line (still searching nearby ASSTs), never
#    "registro lento"
#  - partner times in hand -> shown, not the waiting list
# Run: $PY -I tests/bc_after_consent.py booking_centre/agent tests/bc_test.py
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
A._PARTNER_SETTLE = 0.01; A._PARTNER_WAIT = 0.1; A._PARTNER_POLL = 0.01; A._RARE_WAIT = 0.1
A._SLOW_WAIT = 0.2; A._SLOW_REASK = 0.1; A._SLOW_POLL = 0.01
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:260]}")

PA = "agent:part-a"
def poff(slot):
    return (f"offer offer_id=po-{slot} slot_id={slot} doctor_id=asst-y-h1 facility={PA} procedure=VIS-FIS "
            f"agenda_date=2026-11-03T10:30:00+00:00 agenda_day=tue")

async def say(c, sender, text):
    m = c.add(sender, BC, text); c.inbound = m; c.out.clear()
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    return [t for to, t in c.out if to == CIT]

async def consented(drop_waiting):
    """A case where the citizen consented to the partner search. With drop_waiting the
    consent turn's waiting list is removed: live, the city's latency ended that turn before
    the partners' wait was over, so nothing at all had been offered."""
    peers = [Peer(agent_id=PA, role="facility", capabilities=("hospital.physiatry",))]
    c = FakeCity(slots=[], peers=peers)
    await say(c, CIT, "prenoto prescription_number=rx-1")
    await say(c, CIT, "data.response purpose=cross_asst")
    if drop_waiting:
        c.rows = [r for r in c.rows if "waiting_list=true" not in r.text]
    return c

async def main():
    c = await consented(drop_waiting=True)
    later = await say(c, CIT, "Gentile signorina, con questo ginocchio non riesco a godermi il Duomo, ho pochissimo tempo")
    check("nothing offered after consent: the next message gets the waiting list", any("waiting_list=true" in t for t in later), str(later))
    check("...and no 'registro lento'", not any("registro" in t for t in later), str(later))
    again = await say(c, CIT, "allora?")
    check("on the waiting list: honest line, not 'registro lento'", again and not any("registro" in t for t in again) and any("ASST vicine" in t for t in again), str(again))
    check("on the waiting list: not offered twice", not any("waiting_list=true" in t for t in again), str(again))

    c = await consented(drop_waiting=False)
    later = await say(c, CIT, "allora, novità?")
    check("waiting list already sent: honest line only", later and not any("registro" in t for t in later) and not any("waiting_list=true" in t for t in later), str(later))

    c = await consented(drop_waiting=True)
    c.add(PA, BC, poff("P1"))
    later = await say(c, CIT, "allora, ci sono posti?")
    check("partner time in hand: shown instead of the waiting list", any("slot_id=P1" in t for t in later) and not any("waiting_list=true" in t for t in later), str(later))
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
