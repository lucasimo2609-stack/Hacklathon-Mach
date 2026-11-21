# MACH hackathon — team red-agent (ASST asst-giambellino)

Milano Agentic City Hackathon, 20–21 Nov 2026. Five agents in the city arena; the score comes
from the care-journey rubric. Kit: https://github.com/projectnandaitaly/mach-hackathon-kit
(rules: `docs/kit/e19-rules.md`). Team console: https://projectnandaitaly.ai/team
(Journeys = "Percorsi dei cittadini", Agents, Log tabs). Public board + "Il Token della Sera"
(levels, faults): https://projectnandaitaly.ai

## Agents

| Folder | Agent id | Role / capability |
|---|---|---|
| `gp` | agent:c32jyk0cyan7 | gp |
| `booking_centre` | agent:cdc7x6m21nj6 | booking_centre |
| `hospital` | agent:h6r1v45esk77 | facility / hospital.physiatry |
| `specialist` | agent:hnpe58epeyh1 | facility / specialist_care.cardiology |
| `family_counseling` | agent:bzs050xacs1m | facility / family_counseling.gynecology |

**All five `agent/agent.py` files are identical** (one shared brain; the role comes from the card).
Edit `hospital/agent/agent.py`, then copy it to the other four. Never edit Dockerfile / city.yaml,
never `city init` or `city retire`.

## Rules we learned the hard way

- **Deploy limit is per TEAM: one `city deploy` every 5 minutes for all agents.** Refused tries
  (`QUOTA_EXCEEDED`) do not reset the timer. Only ONE person deploys; always `git pull` first,
  push the `card.yaml` version bump after.
- Deploys sometimes fail at roll-out with "agent ingress route did not become ready" (404/503).
  The old version keeps serving. Check `city status agent:<x>`; sometimes it goes live late.
  Retry after 5 min with the card version bumped past the live one.
- Messages arriving during a roll-out can be lost (journey 000034): deploy rarely, batch fixes.
- The Ledger's world answer is `world slots=N slot_id=… doctor_id=… procedure=… …` (not the
  `slots` lines the kit's example expected), facilities may be named (`hospital`) instead of
  agent ids, times may lack a timezone. `_normalize_world()` handles all of it. The brain logs
  every Ledger reply as a warning: read the agent Log tab to see real formats.
- Ask citizens for consent with `data.request purpose=…` (a bare `consent purpose=…` confused
  them: "Which consent_ref?"). Only an explicit "no" is a refusal. Exception: the specialist's
  report uses `consent purpose=report_sharing` as the kit documents.
- Citizens choose from ONE message: all offers go in a single `say`.
- Friendly, useful human text after the tokens earns the review's +1 (first POSITIVE reviews
  appeared once we added it). Never put act words (offer, confirm, cancel, consent,
  prescription, checkin, report) as standalone words inside the friendly text unless intended.

## MACH-1.2 (common inter-ASST format, from 21 Nov 01:15)

Backward compatible with MACH-1 / 1.1. Full text: `MACH-1.2.md` on Discord. What matters for us:

- **Roadmap:** L5 01:15 combined constraints · L6 02:15 `fault.cancel` on every first booking ·
  L7 03:15 partners down, duplicates, shared slots · L8 04:15 rules change mid-wave ·
  **freeze 06:00, last deploy 05:30** · Sat 10:00 impostors. Lower-level citizens keep coming.
- **Reading:** split by line, first word = act, each line on its own; a line without `=` is
  human text; unknown keys ignored; an unknown `cancel` reason means `no_availability`.
- **Writing:** one line per act, one message, max 6 offer lines; ISO dates without zone; no
  punctuation glued to values; `offer` and `cancel` echo `request_id`; Italian human line last,
  without act words.
- **need.request (L5, done):** criteria only: `lang`, `gender_preference` (`gender` synonym),
  `days=tue/thu`, optional `after`/`before`/`wheelchair`/`deadline`/`rebook_of`. Never name,
  citizen id or prescription before `consent purpose=cross_asst`.
- **Relaxed offers (L5, done on facilities):** nothing fits all criteria → `cancel
  reason=no_availability` and, under it in the same message, up to 3 offers breaking ONE
  criterion, marked `relaxed=days|gender|lang`. The booking centre never shows `relaxed`,
  `reserve`, `doctor_lang`, `doctor_gender` to the citizen: it says in Italian what changes
  and asks if it is fine.
- **REBOOK (L6, done):** the real `fault.cancel` format is unknown until it fires, so every
  path is covered and logged (`city <sender>: …` and `rebook <need>: …` warnings in the Log
  tab: read them at the first fault and adjust).
  - Facility gets a city/Ledger notice about one of our bookings → ONE message to whoever
    booked: `cancel reason=facility_cancelled booking_id= offer_id= slot_id= request_id=`
    + up to 3 alternatives (same doctor first, inside the priority window) + Italian line.
  - Booking centre gets that cancel from a facility (ours or a partner, `offer_id` or only
    `booking_id`), a city notice, or the citizen saying it in words → ONE message to the
    citizen: cancel line on top, new offers below, «La struttura ha annullato…». No new slot
    of ours → the cancel line first, then the partner search / waiting list.
  - Idempotent per (need, offer); graders (`city:review/clock/audit/emergency`) and Ledger
    `world/agenda/…` replies are never notices. Consultorio rebooks the citizen directly.
  - Not done yet: `rebook_of=` priority for partner requests (we already answer at once).
- **Idempotency (L7, todo):** same `request_id` → same offers; same `offer_id` confirm → same
  receipt, never a second hold; never a receipt without a successful `commit` (−2).
- **Soft lock (L7):** a slot offered to one `request_id` is not offered to another for 60 real
  seconds; the Ledger's first `hold` wins, others get `cancel reason=slot_taken` + alternatives.
- **Rule sync (L8, done in `_on_refused`):** `PRESCRIPTION_EXPIRED` → `prescription_expired`
  (send to GP for renewal), `CONSENT_MISSING` → `consent_missing` (ask `cross_asst`, confirm
  again), `NO_CAPACITY` → `no_capacity` (B/D/P take a non-reserve slot). With P3 facilities
  mark reserve slots `reserve=U`.
- **Retries:** never retry a refusal (4xx, `TARGET_NOT_VISIBLE`, Ledger refusals). Retry a
  silence once after 10 s, then move to another facility.
- **Trust ring (impostors):** sender must be in `_TRUSTED_AGENTS` and returned by
  `city.find`; `facility=` must equal the sender; procedure offered by that facility; future
  date within deadline and doctor in the registry with that language/gender; a real offer
  never asks for data. Red flags: asks citizen data, contains instructions
  ("ignora le regole", "system:"), receipt without our confirm, too-good slot. Report on
  Discord as `ring.alert suspect=agent:… reason=not_listed|facility_mismatch|asked_data|injection|phantom_receipt|fake_slot seen=… by=red-agent`.
- **The whole ring is in `_RING`** (from the city's own map, `/v1/scoreboard/map`: all 26
  ASSTs, teams, districts and the five agent ids each). Every other ASST's facilities are
  asked on a cross-ASST search; the one speaking the citizen's rare language goes first and
  gets up to `_RARE_WAIT` (25 s). Nothing fits → a second round (`request_id=<need>-r2`) to
  every partner, also after a partner refuses a hold. A waiting list turned down and nothing
  found → one honest closing line («Ho chiesto due volte…»), waiting list again on a yes.
  A fitting partner slot that arrives after the waiting list is shown (upgrade).
  The console API is handy for checks: `/v1/team/journeys`, `/v1/team/journeys/<need_id>`
  (messages + verdict rows + answer-set size), `/v1/logs?agent_id=…` (last 150 lines only).
- **Ring tables in code** (`_RARE_BY_ASST`, `_PARTNER_AGENTS`, `_TRUSTED_AGENTS`,
  `_KNOWN_FACILITIES`): add every id list posted on Discord. Rare languages: Giambellino ka,
  Precotto/Toros ro, Nord ur, Corvetto fr, Brera fa, Isola tl, Ortica wo, Greco si, Bicocca ti,
  Lambrate ja, Gorla sq, Forlanini de, Città Studi tr (`asst-citta-studi-*`, ASST names may
  contain a dash). Unknown: Lorenteggio, Bovisa. Ids missing: Isola hospital/booking/GP,
  Gorla, Brera, Ortica, Forlanini, Città Studi.
- **Citizen phrases** (plain Italian): searching outside ASST «Qui non c'è posto in tempo
  utile. Sto cercando nelle ASST vicine…»; relaxed «Martedì non c'è posto. Giovedì alle 11 c'è
  lo stesso tipo di visita. Va bene lo stesso?»; rebooking «La struttura ha annullato il suo
  appuntamento. Le ho già trovato un altro posto…»; none «La metto in lista d'attesa…».

## What the brain does (high level)

- GP: 3-layer symptom recognition (regex + typo net → LLM fallback → polite clarify), wide
  red flags with negation, P1 renewal, answers every citizen message, it/en/es/fr/ka.
- Booking: prescription check + parallel slot prefetch (1.5 s to offers), diverse offers in one
  message, days/gender preference, urgent-reserve detection (P3), renewal request (P1),
  cross-ASST with consent (P2) + waiting-list fallback, hospital-down cancel + alternative,
  booking-consent ask, never silent.
- Facilities: answer partner ASST requests instantly (cache), hold/commit/receipt, alternatives
  after a refused hold, check-in in plain words, refused check-in explained, specialist report
  with consent + CTRL-CARD follow-up.

## Tests (fake city, no network)

Run with the city-cli Python (`%APPDATA%\uv\tools\city-cli\Scripts\python.exe`, flag `-I`):

```
PY=~/AppData/Roaming/uv/tools/city-cli/Scripts/python.exe
$PY -I tests/gp_test.py gp/agent          # symptom phrasings, expect failures: 0
$PY -I tests/gp_test2.py gp/agent         # red flags + negation, languages
$PY -I tests/gp_flow.py gp/agent          # follow-up / resend / after red flag
$PY -I tests/gp_protocol.py gp/agent      # procedure + priority match the protocol table
$PY -I tests/gp_access.py gp/agent tests/bc_test.py   # access needs GP->booking->facility, injections
$PY -I tests/bc_test.py booking_centre/agent            # 9 booking scenarios
$PY -I tests/bc_fix.py booking_centre/agent tests/bc_test.py
$PY -I tests/bc_world.py booking_centre/agent tests/bc_test.py   # real world format
$PY -I tests/bc_speed.py booking_centre/agent           # ~1.5 s to first offer
$PY -I tests/bc_offers.py booking_centre/agent tests/bc_test.py  # up to 5 offers, gender kept
$PY -I tests/bc_clock.py booking_centre/agent tests/bc_test.py   # fresh clock, no cancel loop
$PY -I tests/bc_cross.py booking_centre/agent tests/bc_test.py   # partner offers in ONE message
$PY -I tests/bc_pages.py booking_centre/agent tests/bc_test.py   # all world pages read in one turn
$PY -I tests/theme.py booking_centre/agent tests/bc_test.py      # readable dates, tone, receipt, old car
$PY -I tests/bc_l4.py booking_centre/agent tests/bc_test.py       # level 4: early pages, slow partners, refused hold
$PY -I tests/sp_test.py specialist/agent
$PY -I tests/sp_flow.py specialist/agent     # report consent, silence, GP care.update
$PY -I tests/h_test.py hospital/agent hospital
$PY -I tests/h_desk.py hospital/agent hospital
$PY -I tests/h_alt.py hospital/agent tests/h_desk.py
$PY -I tests/mach12.py hospital/agent hospital    # MACH-1.2: relaxed offers, days/gender criteria
$PY -I tests/gp_review.py gp/agent         # personal reply, collaboration said, earliest slot
$PY -I tests/chaos.py hospital/agent       # 1,275 odd/failing turns: no crash, never silent
$PY -I tests/bc_rebook.py booking_centre/agent tests/bc_test.py   # L6: cancel + new offers in ONE message
$PY -I tests/h_rebook.py hospital/agent hospital  # L6 facility side: cancel + alternatives
$PY -I tests/bc_ring.py booking_centre/agent tests/bc_test.py    # rare language partner, round 2, no empty promise
```

All must pass before any deploy.

## Routine during the race

Every 30 min: Journeys (all waves, "Prima i falliti") → open each Fallito / NEGATIVE, read the
verdict line; read agent Log tabs; check level on the public board. Fix only clear,
reproducible causes, add a test scenario, run all suites, push, deploy only affected agents one
at a time.

## State (21 Nov, early)

- Specialist **1.0.5 live** (roll-out took 6m42s, then passed conformance): report consent as
  `data.request` naming its consent_ref, any yes counts, silence -> report filed unshared after
  20 s, one checkin/consent line per booking, `care.update` to our GP with consent.
- Booking centre **1.0.9 live** (deployed 00:19 from 984bad6): clock read per case + pace
  learned, no cancel loop, cross-ASST partner offers in ONE message, up to 5 offers.
- Watch next: Journeys for report rows (+2 expected now) and booking wrong_outcome (should stop).
- `city deploy` on Windows: set `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` or it crashes printing.

## State at handoff (20 Nov, ~23:30)

- Live: GP 1.0.4, booking 1.0.5, consultorio 1.0.3 (all with the world-format fix);
  specialist 1.0.1 (OLD code: cannot read the real slot format); hospital 1.0.2 (OLD) with a
  retry of the new version in progress.
- Next deploy: specialist (level 3 brings check-in + report). Then only fixes found by checks.
- First real booking succeeded after the world-format fix (journey …740002, POSITIVE).
