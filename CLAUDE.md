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
