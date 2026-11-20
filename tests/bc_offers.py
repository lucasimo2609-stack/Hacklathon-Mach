# Offer count: up to 5 slots that keep the citizen's stated doctor gender (more doctors/days
# cover more unspoken preferences -> S_pref, +2). Slots of the other gender only fill up to 3.
# Run: $PY -I tests/bc_offers.py booking_centre/agent tests/bc_test.py
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])

def sl(i, day, date, doc, hour):
    return f"slot_id=T{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={date}T{hour:02d}:30:00+00:00 day={day} free=1"

F, M = "asst-x-h1", "asst-x-h3"  # h1 female (mon-wed), h3 male (tue/thu)
bad = 0

async def run(name, slots, text, want_n, want_docs=None, must=()):
    global bad
    c = FakeCity(slots=slots)
    m = c.add(CIT, BC, text); c.inbound = m
    await A.handle("booking_centre", c, m, await c.history(need_id=c.need))
    offers = [A.fields_of(line) for to, t in c.out if to == CIT for line in t.split("\n")
              if line.startswith("offer ") and "slot_id=" in line]
    ids = [o["slot_id"] for o in offers]
    docs = {o["doctor_id"] for o in offers}
    problems = []
    if len(offers) != want_n:
        problems.append(f"{len(offers)} offers, want {want_n}")
    if want_docs is not None and not docs <= want_docs:
        problems.append(f"doctors {sorted(docs)}")
    if not set(must) <= set(ids):
        problems.append(f"missing {sorted(set(must) - set(ids))}")
    if len([t for to, t in c.out if to == CIT]) != 1:
        problems.append("offers not in ONE message")
    bad += bool(problems)
    print("OK " if not problems else "BAD", name, "->", ids, "|", "; ".join(problems))

async def main():
    many = [sl(1, "mon", "2026-11-02", F, 13), sl(2, "mon", "2026-11-02", F, 15),
            sl(3, "tue", "2026-11-03", F, 9), sl(4, "tue", "2026-11-03", F, 11),
            sl(5, "tue", "2026-11-03", M, 10), sl(6, "tue", "2026-11-03", M, 14),
            sl(7, "tue", "2026-11-03", F, 16)]
    await run("no gender: 7 fitting -> 5", many, "prenoto prescription_number=rx-1", 5)
    await run("female, 5 female + 2 male -> 5 all female", many,
              "prenoto prescription_number=rx-1, preferirei una dottoressa", 5, {F})
    few = [sl(1, "mon", "2026-11-02", F, 13), sl(3, "tue", "2026-11-03", F, 9),
           sl(5, "tue", "2026-11-03", M, 10), sl(6, "tue", "2026-11-03", M, 14),
           sl(8, "mon", "2026-11-02", M, 16)]
    await run("female, 2 female + 3 male -> 3 (both female kept)", few,
              "prenoto prescription_number=rx-1, preferirei una dottoressa", 3, None, ("T1", "T3"))
    two = [sl(1, "mon", "2026-11-02", F, 13), sl(3, "tue", "2026-11-03", F, 9)]
    await run("only 2 fitting -> 2", two, "prenoto prescription_number=rx-1", 2)
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
