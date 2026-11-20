# The Ledger pages its slot list from the world's first week, so this week's slots sit on later
# pages. Journeys 910005/340002/000141 (20 Nov, English, priority B): "no suitable slot in our
# ASST" while h1 had Monday/Tuesday free -> waiting list -> wrong_outcome -1, and ~40 s replies.
# Run: $PY -I tests/bc_pages.py booking_centre/agent tests/bc_test.py
import asyncio, sys, time
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, ("| " + info) if info and not ok else "")

def sl(i, date, hour, doc, day):
    return f"slot_id=P{i} doctor_id={doc} facility={HOSP} procedure=VIS-FIS at={date}T{hour:02d}:30:00+00:00 day={day} free=1"

PAGES = {
    1: [sl(1, "2026-10-26", 10, "asst-x-h1", "mon"), sl(2, "2026-10-27", 10, "asst-x-h1", "tue")],      # past week
    2: [sl(3, "2026-11-09", 10, "asst-x-h1", "mon"), sl(4, "2026-11-10", 10, "asst-x-h1", "tue")],      # too late for B
    3: [sl(5, "2026-11-02", 13, "asst-x-h1", "mon"), sl(6, "2026-11-03", 10, "asst-x-h1", "tue"),
        sl(7, "2026-11-03", 11, "asst-x-h3", "tue")],                                                   # this week
}

class Paged(FakeCity):
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "world" and f.get("procedure") == "VIS-FIS":
            page = int(f.get("page", "1"))
            s.add(LEDGER, BC, f"slots page={page}/3 procedure=VIS-FIS\n" + "\n".join(PAGES.get(page, [])))
        elif head == "world":
            s.add(LEDGER, BC, f"slots page=1/1 procedure={f.get('procedure')}")
        else:
            super().ledger(text)

async def main():
    A._AGENDA_SEEN = None
    c = Paged(slots=[])
    t = time.monotonic()
    await turn(c, CIT, "Hello, I need a quick back pain appointment with an English-speaking doctor please. prescription_number=rx-1 lang=en")
    took = time.monotonic() - t
    offers = [o for to, x in c.out if to == CIT for o in A._offers_in(x)]
    ids = [o.get("slot_id") for o in offers]
    asked = [x for to, x in c.out if to == LEDGER and x.startswith("world procedure=VIS-FIS")]
    check("this week's English slots offered from page 3", set(ids) == {"P5", "P6"}, str(ids))
    check("no cross-ASST / waiting list", not any("cross_asst" in x or "waiting_list" in x for to, x in c.out if to == CIT))
    check("all pages asked in the same turn", {"page=2", "page=3"} <= {p for x in asked for p in x.split() if p.startswith("page=")}, str(asked))
    check("answer in the same turn, fast", took < 3.0, f"{took:.2f}s")
    check("italian-only h3 not offered to an English citizen", "P7" not in ids)
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
