"""Duplicate confirms on a facility that books directly (21 Nov, wave W01QQQ ...360007: the
citizen sent two identical confirms in the same second). Both turns reached the hold before
either was in the case: two holds on one slot, the second refused SLOT_TAKEN on its own turn,
risking a 'slot taken' message for a slot we had just booked.
Expect: one hold, one commit, one receipt, no cancel to the citizen.
Run: tests/h_dup_confirm.py family_counseling/agent family_counseling"""
import asyncio, sys, itertools, os
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
os.environ["CITY_ROLE"] = sys.argv[2]
import agent as A
from city_sdk.city import Message, CapError, LEDGER
A._PULL_PAUSE = 0.01
ids = itertools.count(1); CIT = "citizen:t/9"
ME = {"family_counseling": "agent:bzs050xacs1m", "hospital": "agent:h6r1v45esk77"}[sys.argv[2]]
BC = "agent:cdc7x6m21nj6"
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:300]}")
class C:
    def __init__(s):
        s.need = f"N-{next(ids)}"; s.rows = []; s.out = []; s.holds = 0
    agent_id = property(lambda s: ME); address = ""
    def add(s, a, b, t):
        m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b)
        s.rows.append(m); return m
    async def say(s, to, text, status=None):
        s.add(ME, to, text); s.out.append((to, text))
        if to == LEDGER:
            f = A.fields_of(text); h = text.split()[0]
            async def later(t):
                await asyncio.sleep(0.4); s.add(LEDGER, ME, t)
            if h == "hold":
                s.holds += 1
                line = f"held hold_id=H1 slot_id={f['slot_id']}" if s.holds == 1 else "refused op=hold code=SLOT_TAKEN"
                asyncio.ensure_future(later(line))
            if h == "commit":
                asyncio.ensure_future(later(f"committed booking_id={f['hold_id']} ledger_ref=L1 slot_id=C1"))
        return "x"
    async def history(s, peer=None, *, need_id=None): return list(s.rows)
    async def find(s, q): return []
    async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
def tally(c, to):
    led = [t for t2, t in c.out if t2 == LEDGER]
    return (sum(x.startswith("hold ") for x in led), sum(x.startswith("commit ") for x in led),
            [t for t2, t in c.out if t2 == to and t.startswith("booking.receipt")],
            [t for t2, t in c.out if t2 == to and (t.startswith("cancel") or "SLOT_TAKEN" in t or "slot_taken" in t)])
async def main(role):
    if role == "family_counseling":
        # 1. Two identical citizen confirms, same instant.
        c = C()
        c.add(ME, CIT, f"offer offer_id=of-C1 slot_id=C1 doctor_id=asst-giambellino-c1 facility={ME} procedure=CONS-GIN agenda_date=2026-11-04T10:30:00")
        t = "confirm consent_ref=cons-N-booking offer_id=of-C1"
        m1 = c.add(CIT, ME, t); m2 = c.add(CIT, ME, t); h = await c.history()
        await asyncio.gather(A.handle(role, c, m1, list(h)), A.handle(role, c, m2, list(h)))
        holds, commits, rec, neg = tally(c, CIT)
        check("same-instant duplicate: one hold", holds == 1, str(holds))
        check("same-instant duplicate: one commit", commits == 1, str(commits))
        check("same-instant duplicate: one receipt", len(rec) == 1, str(rec))
        check("same-instant duplicate: no cancel / slot_taken to the citizen", not neg, str(neg))
        # 2. The citizen repeats the confirm after the receipt: no second hold.
        m3 = c.add(CIT, ME, t)
        await A.handle(role, c, m3, await c.history())
        holds2, _, _, neg2 = tally(c, CIT)
        check("repeat after the receipt: still one hold", holds2 == 1, str(holds2))
        check("repeat after the receipt: no cancel", not neg2, str(neg2))
        last = [x for to, x in c.out if to == CIT][-1]
        check("repeat after the receipt: the same receipt again, not 'arriva tra pochi secondi'",
              last.startswith("booking.receipt") and "pochi secondi" not in last, last)
        # 3. A NEW offer confirmed after a receipt (rebook after a facility cancel) books it.
        c.add(ME, CIT, f"offer offer_id=of-C2 slot_id=C2 doctor_id=asst-giambellino-c1 facility={ME} procedure=CONS-GIN agenda_date=2026-11-05T10:30:00")
        m4 = c.add(CIT, ME, "confirm consent_ref=cons-N-booking offer_id=of-C2")
        c.holds = 0  # the Ledger accepts the new slot
        await A.handle(role, c, m4, await c.history())
        new_holds = [x for to, x in c.out if to == LEDGER and x.startswith("hold ") and "slot_id=C2" in x]
        check("new offer after a receipt: a hold for the new slot", len(new_holds) == 1, str(new_holds))
    else:
        # 3. Hospital: the booking centre confirms the same offer twice at once.
        c = C()
        c.add(ME, BC, f"offer offer_id=of-H1 slot_id=C1 doctor_id=asst-giambellino-h1 facility={ME} procedure=VIS-FIS agenda_date=2026-11-04T10:30:00 request_id=N-1")
        t = f"confirm offer_id=of-H1 slot_id=C1 citizen={CIT} consent_ref=cons-N-booking facility={ME} prescription_number=rx-1 request_id=N-1"
        m1 = c.add(BC, ME, t); m2 = c.add(BC, ME, t); h = await c.history()
        await asyncio.gather(A.handle(role, c, m1, list(h)), A.handle(role, c, m2, list(h)))
        holds, commits, rec, neg = tally(c, BC)
        check("booking confirms twice at once: one hold", holds == 1, str(holds))
        check("booking confirms twice at once: one commit", commits == 1, str(commits))
        check("booking confirms twice at once: no cancel / slot_taken to the booking centre", not neg, str(neg))
    print("failures:", bad)
asyncio.run(main(sys.argv[2]))
