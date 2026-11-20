import sys
sys.path.insert(0, sys.argv[1])
sys.stdout.reconfigure(encoding="utf-8")
import agent as a
from city_sdk.city import clinical
flags = {
 "Ho un gran dolore al petto": True,
 "male al petto da stamattina": True,
 "dolore toracico forte": True,
 "mi fa male il petto": True,
 "my chest hurts a lot": True,
 "non sento più le gambe": True,
 "ho le gambe deboli, mal di schiena": True,
 "perdita di forza alle gambe": True,
 "raga dolore al petto assurdo lowkey": True,
 "nessun dolore al petto, solo palpitazioni": False,
 "non ho dolore al petto ma il cuore batte forte": False,
 "no chest pain, just my heart racing": False,
 "ho mal di schiena da settimane": False,
 "il ginocchio mi fa male e non riesco a camminare bene": False,
 "Sento il cuore che batte forte. Posso venire per un controllo?": False,
 "tengo dolor en el pecho": True,
}
bad = 0
for t, want in flags.items():
    got = a._red_flag(t); bad += got != want
    print("OK " if got == want else "BAD", got, "|", t)
print("red-flag failures:", bad)
for t in ["I have back pain please help", "tengo dolor de espalda, por favor", "bonjour, j'ai mal au dos depuis une semaine", "ზურგი მტკივა", "ho mal di schiena"]:
    print(a._speaks_as(t), a._keyword_symptom(t), "|", a._rx_note(t)[:70])
t = "ho mal di schiena, che antidolorifico prendo e a che dose?"
print("clinical:", clinical(t), "symptom:", a._keyword_symptom(t), "| note:", a._rx_note(t)[-90:])
print(a._fresh_rx("N-2026-11-02-890917000013", "7d291a90-4fba-4512-a6cf-6519baeb7516", "R"))
