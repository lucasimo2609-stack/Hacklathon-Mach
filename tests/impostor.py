# Sat 10:00 impostors: an agent outside the ring (real-format id, not on the city map at 01:45)
# gets no slots, its confirm holds nothing, its offers never reach the citizen.
# Run: python -I tests/impostor.py hospital/agent hospital
import asyncio, sys
exec(open("tests/h_test.py", encoding="utf-8").read().split("async def main")[0])
fails = 0
def ok(cond, msg):
    global fails
    print(("OK  " if cond else "FAIL"), msg); fails += (not cond)
FAKE = "agent:zzzz9999zzzz"
REAL = "agent:x0vr9rbwpesr"  # Corvetto hospital... used as a ring booking centre stand-in
async def main(role):
    A._WORLD_SEEN.clear(); A._PARTNER_OFFERED.clear()
    c = C([slot(1, "tue", "2026-11-03"), slot(2, "wed", "2026-11-03")])
    await turn(c, FAKE, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=X1", role)
    ok(not [t for to, t in c.out if to == FAKE], "impostor gets no slots")
    await turn(c, FAKE, "confirm offer_id=of-S1 slot_id=S1 citizen=citizen:x/1 consent_ref=c prescription_number=rx facility=agent:hosp", role)
    ok(not any(r.sender == ME and r.text.startswith("hold") for r in c.rows), "impostor confirm holds nothing")
    await turn(c, REAL, "need.request service_type=hospital.physiatry procedure=VIS-FIS priority=B request_id=R1", role)
    ok(any("offer" in t for to, t in c.out if to == REAL), "a ring member still gets offers")
    ok(not A._ring_member(FAKE) and A._ring_member(REAL) and A._ring_member("agent:part-a"), "ring membership")
    ranked = A._rank_partner_offers([(FAKE, {"slot_id": "F", "agenda_date": "2026-11-03T09:00:00"}), (REAL, {"slot_id": "R", "agenda_date": "2026-11-03T10:00:00"})], "it")
    ok([s for s, _ in ranked] == [REAL], "impostor offers dropped before the citizen sees them")
    # GP: no prescription details for an impostor; a ring booking centre still gets them
    c = C([])
    await turn(c, FAKE, "check prescription_number=prescription_number-N-1 please", "gp")
    ok(not [t for to, t in c.out if to == FAKE], "GP tells an impostor nothing")
    await turn(c, REAL, "check prescription_number=prescription_number-N-1 please", "gp")
    ok([t for to, t in c.out if to == REAL], "GP still answers a ring agent")
    # booking: a cancel only from the facility behind the offer
    chat = [A.Message(type="chat", sender="agent:cdc7x6m21nj6", msg_id="m1", need_id="N", conversation_id="N",
                      body={"text": "offer offer_id=po-1 slot_id=P1 doctor_id=asst-corvetto-h1 facility=" + REAL + " procedure=VIS-FIS"},
                      recipient="citizen:t/1")]
    A._our_offer_backup = A._our_offer
    A._our_offer = lambda chat, agent, oid: {"offer_id": "po-1", "slot_id": "P1", "via": REAL, "facility": REAL} if oid == "po-1" else {}
    ok(A._cancel_from_owner(chat, "agent:cdc7x6m21nj6", REAL, "po-1"), "the partner behind the offer may cancel it")
    ok(not A._cancel_from_owner(chat, "agent:cdc7x6m21nj6", FAKE, "po-1"), "an impostor may not cancel our citizen's booking")
    ok(not A._cancel_from_owner(chat, "agent:cdc7x6m21nj6", "agent:gdrf9b9kxxss", "po-1"), "another ring agent may not cancel it either")
    ok(A._cancel_from_owner(chat, "agent:cdc7x6m21nj6", "agent:h6r1v45esk77", "po-1"), "our own facility may")
    A._our_offer = A._our_offer_backup
    print("failures:", fails)
asyncio.run(main(sys.argv[2]))
