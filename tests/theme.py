# Theme features on top of the care journey (tokens unchanged): readable dates, tone, cognitive
# wording, receipt directions + paperless, old car, GP tone. Run:
#   $PY -I tests/theme.py booking_centre/agent tests/bc_test.py
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, ("| " + info[:300]) if info and not ok else "")

def offers_msg(c):
    return next((t for to, t in c.out if to == CIT and "offer offer_id=" in t), "")

# 21 Nov: the booking keeps 8 h ahead for B/D (U unchanged): Monday 10:30 at 08:00 is too close,
# the first time offered is Tuesday 10:30.
async def main():
    # 1. Readable dates + weekday, tokens untouched
    c = FakeCity(slots=own); await turn(c, CIT, "vorrei prenotare prescription_number=rx-1 lang=it")
    m = offers_msg(c)
    check("dates: readable Italian weekday and month", "Orari: 1) martedì 3 novembre ore 10:30" in m, m[-300:])
    tokens = [l for l in m.split("\n") if l.startswith("offer ")]
    check("dates: offer token lines unchanged", tokens and all(l.split()[1].startswith("offer_id=") and "agenda_date=" in l for l in tokens))
    check("dates: still one message", len([1 for to, t in c.out if to == CIT]) == 1)
    c = FakeCity(slots=own); await turn(c, CIT, "hello I want to book please prescription_number=rx-1 lang=en")
    check("dates: English", "Times: 1) Tuesday 3 November at 10:30" in offers_msg(c), offers_msg(c)[-200:])

    # 2. Tone at the booking centre
    c = FakeCity(slots=own); await turn(c, CIT, "sono molto preoccupata, vorrei prenotare prescription_number=rx-1")
    check("tone: anxious -> reassured first", "Capisco la preoccupazione" in offers_msg(c), offers_msg(c)[-250:])
    c = FakeCity(slots=own); await turn(c, CIT, "too busy, quick: prescription_number=rx-1 lang=en")
    m = offers_msg(c)
    check("tone: curt -> brief line", "Pick a time: reply with its code." in m and "wheelchair access" not in m, m[-200:])

    # 3. Cognitive need -> very simple wording
    c = FakeCity(slots=own); await turn(c, CIT, "prenoto per mia madre, ha l'alzheimer prescription_number=rx-1")
    check("cognitive: very simple wording", "Scelga un orario. Mi scriva il codice. La aiuto io." in offers_msg(c), offers_msg(c)[-200:])
    c = FakeCity(slots=own); await turn(c, CIT, "data.response purpose=booking disability=cognitive prescription_number=rx-1")
    check("cognitive: from the profile field too", "La aiuto io." in offers_msg(c), offers_msg(c)[-200:])

    # 4. Receipt: half-day window, what to bring, paperless; 5. old car
    c = FakeCity(slots=own)
    await turn(c, CIT, "prenoto prescription_number=rx-1. Vengo con la mia auto euro 3")
    await turn(c, CIT, "confirm offer_id=of-S2 consent_ref=cb-1")
    c.out.clear(); await turn(c, HOSP, "booking.receipt booking_id=BK1 ledger_ref=L1")
    r = next((t for to, t in c.out if to == CIT and t.startswith("booking.receipt")), "")
    check("receipt: tokens first and unchanged", r.startswith("booking.receipt booking_id=BK1 ledger_ref=L1 "), r[:80])
    check("receipt: half-day window of the slot (10:30 -> morning)", "08:00-13:00" in r, r)
    check("receipt: what to bring + paperless", "tessera sanitaria" in r and "nessun foglio da stampare" in r, r)
    check("environment: old car -> gentle suggestion", "EURO 0-4" in r and "consiglio" in r, r)
    c = FakeCity(slots=own)
    await turn(c, CIT, "prenoto prescription_number=rx-1 car_euro_class=EURO-6")
    await turn(c, CIT, "confirm offer_id=of-S2 consent_ref=cb-1")
    c.out.clear(); await turn(c, HOSP, "booking.receipt booking_id=BK2 ledger_ref=L2")
    r = next((t for to, t in c.out if to == CIT and t.startswith("booking.receipt")), "")
    check("environment: EURO 6 -> no suggestion", "EURO 0-4" not in r, r)

    # 6. GP tone, prescription tokens unchanged
    class G:
        def __init__(s): s.need = f"N-{next(ids)}"; s.rows = []
        agent_id = property(lambda s: A._GP_AGENT); address = ""
        def add(s, a, b, t):
            m = Message(type="chat", sender=a, msg_id=f"m{next(ids)}", need_id=s.need, body={"text": t}, recipient=b); s.rows.append(m); return m
        async def say(s, to, text, status=None): s.add(A._GP_AGENT, to, text)
        async def history(s, peer=None, *, need_id=None): return list(s.rows)
        async def find(s, q): return []
        async def llm(s, *a, **k): raise CapError("KEY_UNKNOWN", "x")
    A._PROTOCOL_ASKED = True
    for text, want, name in [
        ("Ho tanta paura, il cuore mi batte fortissimo", "Capisco la preoccupazione", "GP: anxious reassured"),
        ("Back pain. Too busy, quick.", "Book at the booking centre with this number.", "GP: curt brief"),
    ]:
        g = G(); m = g.add("citizen:t/5", A._GP_AGENT, text)
        await A.handle("gp", g, m, await g.history())
        rx = next((r.text for r in g.rows if r.sender == A._GP_AGENT and r.text.startswith("prescription ")), "")
        check(name, want in rx and rx.split()[1].startswith("prescription_number="), rx)
    print("failures:", bad)
    sys.exit(1 if bad else 0)

asyncio.run(main())
