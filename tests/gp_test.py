import sys, time
sys.path.insert(0, sys.argv[1])
import agent as a
cases = {
 "ho la schiena a pezzi": "SYM-BACK",
 "ho le palpitazioni": "SYM-PALPITATIONS",
 "il cuore mi va a mille": "SYM-PALPITATIONS",
 "mi batte forte il cuore": "SYM-PALPITATIONS",
 "batticuore da ieri": "SYM-PALPITATIONS",
 "my back hurts so much": "SYM-BACK",
 "visita di controllo cardiologica": "SYM-FOLLOWUP",
 "mi fa male il ginochio": "SYM-KNEE",
 "il ginocchio mi fa male": "SYM-KNEE",
 "raga lowkey la schiena mi sta uccidendo": "SYM-BACK",
 "Io sento cuore che batte veloce. Vorrei controllo, grazie.": "SYM-PALPITATIONS",
 "Sento il cuore che batte forte. Posso venire per un controllo?": "SYM-PALPITATIONS",
 "La prego di voler considerare la possibilità di un controllo, in quanto sento il cuore che batte con insolita intensità.": "SYM-PALPITATIONS",
 "Mi perdoni, è da qualche settimana che ho mal di schiena": "SYM-BACK",
 "vorrei fare un controllo del cuore di routine": "SYM-FOLLOWUP",
 "routine heart check please": "SYM-FOLLOWUP",
 "my heart is racing": "SYM-PALPITATIONS",
 "Ho dolore al ginocchio destro quando salgo le scale": "SYM-KNEE",
 "ho la tachicardia": "SYM-PALPITATIONS",
 "colpo della strega stamattina": "SYM-BACK",
 "palpitazzioni forti": "SYM-PALPITATIONS",
 "grazie mille": None,
 "buongiorno dottore": None,
 "ho mal di testa": None,
}
bad = 0
t = time.perf_counter()
for text, want in cases.items():
    got = a._keyword_symptom(text)
    flag = "OK " if got == want else "BAD"
    bad += got != want
    print(flag, repr(text)[:60], "->", got, "(want", want, ")")
print("per call ms:", round((time.perf_counter()-t)/len(cases)*1000, 3), "| failures:", bad)
print(a._clarify("ho mal di testa")[:60])
