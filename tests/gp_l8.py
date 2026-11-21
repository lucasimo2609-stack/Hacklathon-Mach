# Level 8: red flags hidden in plain words must be escalated (-2 each if missed), and
# the same words negated or harmless must NOT be (a wrong escalation loses the prescription).
# Run: python -I tests/gp_l8.py gp/agent
import sys, os
sys.path.insert(0, sys.argv[1]); os.environ.setdefault("CITY_ROLE", "gp")
import agent as A
RED = [
 "Ho mal di schiena da giorni e stamattina le gambe non mi reggevano più",
 "mi fa male la schiena e da ieri mi cedono le gambe quando cammino",
 "schiena a pezzi, e non sento più bene le gambe, sono come addormentate",
 "mal di schiena, non riesco più a muovere bene le gambe, sono deboli",
 "mal di schiena forte e non riesco a stare in piedi",
 "my back hurts and my legs keep giving way",
 "back pain, and I can't feel my feet properly anymore",
 "Dottore ho il cuore che batte forte e sento una morsa al petto",
 "palpitazioni e un peso sul torace che non passa",
 "heart racing and a crushing feeling in my chest",
 "ho le palpitazioni e sento oppressione",
 "ho il batticuore e un dolore che dal petto va al braccio sinistro",
 "my heart is pounding and there is a pain going into my left arm",
]
CALM = [
 "ginocchio gonfio, ma niente di grave", "ho mal di schiena ma le gambe stanno bene, nessun formicolio",
 "palpitazioni ma nessun dolore al petto", "Ho la schiena bloccata ma cammino normalmente",
 "le gambe stanno bene, è solo la schiena", "non ho problemi alle gambe", "palpitazioni dopo il caffè, nessun dolore",
 "I can walk fine, just back pain", "ho mal di schiena e non riesco a dormire", "nessuna debolezza alle gambe",
 "ginocchio dolorante quando salgo le scale", "my chest is fine, only the heart racing",
]
bad = 0
for t in RED:
    if not A._red_flag(t):
        bad += 1; print("MISSED", t)
for t in CALM:
    if A._red_flag(t):
        bad += 1; print("FALSE ALARM", t)
print("failures:", bad)
sys.exit(1 if bad else 0)
