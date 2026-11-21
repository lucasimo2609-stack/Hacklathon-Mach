"""The lang= token beats the words (W01QQQ: lang=si citizens cancelled English doctors with reason=lang); words decide only without a token. Earlier note: explicit language request beat the profile token (21 Nov ...254/...212/...151: lang=de/ro
citizens asked for "a doctor who speaks English", we searched partners for German/Romanian,
told them "no suitable doctor... just say yes", they asked "Which offer_id, slot_id?" and the
journey stopped). Run: tests/bc_lang_ask.py booking_centre/agent tests/bc_test.py"""
import asyncio, sys
sys.path.insert(0, sys.argv[1]); sys.stdout.reconfigure(encoding="utf-8")
exec(open(sys.argv[2], encoding="utf-8").read().split("async def main():")[0])
bad = 0
def check(name, ok, info=""):
    global bad
    bad += not ok
    print("OK " if ok else "BAD", name, "" if ok else f"| {info[:220]}")
for text, want in (
    ("Could I please book a visit with a doctor who speaks English?", "en"),
    ("Back pain. Need a doctor, English speaker. Fast appointment.", "en"),
    ("could i get an appointment with an english-speaking doc?", "en"),
    ("vorrei un medico anglofono", "en"),
    ("need a doc who speaks my language", ""),
):
    check(f"explicit language: {text[:45]!r} -> {want or 'none'}", A._lang_asked(text) == want, A._lang_asked(text))
# h1 speaks it/en (Tuesday 10:30 is h1's day); h2 italian only.
WORLD = (" slot_id=EN1 doctor_id=asst-giambellino-h1 facility=hospital at=2026-11-17T10:30"
         " slot_id=IT2 doctor_id=asst-giambellino-h2 facility=hospital at=2026-11-18T09:00")
class World(FakeCity):
    def ledger(s, text):
        f = A.fields_of(text); head = text.split()[0]
        if head == "prescription":
            s.add(LEDGER, BC, f"prescription prescription_number={f['prescription_number']} procedure=VIS-FIS priority=B state=issued")
        elif head == "agenda":
            s.add(LEDGER, BC, "agenda agenda_now=2026-11-16T08:00:00+00:00")
        elif head == "world":
            body = WORLD if f.get("procedure") == "VIS-FIS" else ""
            s.add(LEDGER, BC, f"world procedure={f.get('procedure')} page=1/1 slots={2 if body else 0}{body}")
async def main():
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = World(slots=[])
    await turn(c, CIT, "Hello, could I book a visit with a doctor who speaks English? lang=de prescription_number=rx-1")
    sent = " ".join(t for to, t in c.out if to == CIT)
    check("lang=de asking English: the token decides, no English-only h1 offered", "slot_id=EN1" not in sent and "slot_id=IT2" not in sent, sent)
    A._DOWN.clear(); A._AGENDA_SEEN = None; A._WORLD_SEEN.clear()
    c = World(slots=[])
    await turn(c, CIT, "Hello, could I book a visit with a doctor who speaks English? prescription_number=rx-1")
    sent = " ".join(t for to, t in c.out if to == CIT)
    check("no lang token, asks English: our English-speaking h1 offered", "slot_id=EN1" in sent and "slot_id=IT2" not in sent, sent)
    print("failures:", bad)
asyncio.run(main())
