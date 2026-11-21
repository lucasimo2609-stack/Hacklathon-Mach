# Red Agent · ASST Giambellino
## Una sanità che ascolta come vive la persona, non solo cosa sente

Milano Agentic City Hackathon · 20–21 novembre 2026 · squadra red-agent

---

## La vision in una frase

**Il cittadino dice una cosa sola, con le sue parole. La rete fa il resto.**

Chi ha mal di schiena, 82 anni, nessuna macchina e una nipote che lo accompagna non deve compilare moduli né ripetere la sua storia a ogni sportello. Lo dice una volta al medico di base, nella sua lingua. Da lì cinque agenti che collaborano portano quell'informazione, e solo quella necessaria, fino alla porta dell'ambulatorio.

---

## I cinque agenti, un solo cervello

| Agente | Ruolo | Cosa fa per il cittadino |
| --- | --- | --- |
| **Medico di base** | Primo contatto | Capisce il sintomo dalle parole del cittadino, riconosce le emergenze, prescrive secondo protocollo e avvisa il centro prenotazioni |
| **Centro prenotazioni** | Regia del percorso | Trova il posto giusto: nella propria ASST, altrimenti nelle altre 25, con il consenso del cittadino |
| **Ospedale** (fisiatria) | Struttura | Offre i posti, prenota sul registro regionale, accoglie al check-in |
| **Specialista** (cardiologia) | Struttura | Come l'ospedale, più il referto condiviso solo con consenso |
| **Consultorio** (ginecologia) | Struttura | Prenota e accoglie direttamente il cittadino |

Tutti e cinque eseguono lo stesso codice: il ruolo viene dalla carta d'identità dell'agente. Una correzione vale per tutta la filiera nello stesso momento.

---

## 1. Accessibilità: nessuno resta fuori per come parla o per come vive

### Il cittadino descrive la sua vita, l'agente capisce il bisogno

Il medico di base legge nel messaggio del cittadino **nove bisogni**, in italiano, inglese, spagnolo e francese, anche senza accenti e con errori di battitura:

| Bisogno | Esempi di frasi riconosciute |
| --- | --- |
| Accesso senza barriere | "uso la carrozzina", "non riesco a camminare", "deambulatore", "stampelle" |
| Spostamenti difficili | "non ho la macchina", "uso i mezzi pubblici", "abito lontano" |
| Udito | "non sento bene", "apparecchio acustico" |
| Vista | "ipovedente", "non vedo bene" |
| Chi accompagna | "è per mia madre", "per conto di", "badante" |
| Persona anziana | "anziano", "ho 82 anni" |
| Interprete | "non parlo bene l'italiano", "parlo solo…" |
| Difficoltà a capire | "faccio fatica a capire", "problemi di memoria" |
| Fretta | "il prima possibile" |

**Una negazione non conta:** "non ho bisogno dell'interprete" non attiva l'interprete. Se il bisogno viene detto più tardi ("ah, uso la carrozzina"), viene passato avanti comunque e il cittadino se lo sente confermare.

### Il bisogno viaggia con la prenotazione

1. Il medico di base lo **ripete al cittadino** con parole sue, per fargli sapere che è stato ascoltato.
2. Lo passa al centro prenotazioni nell'avviso di presa in carico.
3. Il centro prenotazioni lo **porta alla struttura** insieme alla prenotazione.
4. Al check-in la struttura **accoglie di conseguenza**:
   - carrozzina: «L'ingresso è senza barriere: il personale la accompagna.»
   - udito: «Le scriveremo tutto, senza chiamate a voce.»
   - vista: «Il personale la accompagna fino all'ambulatorio.»
   - difficoltà a capire: «Si sieda pure. La chiamiamo noi.»
   - accompagnatore: «Chi la accompagna può restare con lei.»

### La lingua

- Testi completi per il cittadino in **italiano, inglese, francese e spagnolo**. I messaggi chiave (emergenza, ricetta, rinnovo, richiesta di chiarimento) anche in **georgiano**, la lingua rara della nostra ASST.
- Ogni ASST della città ha una lingua rara. Il centro prenotazioni conosce la mappa di **14 lingue**: singalese a Greco, wolof a Ortica, giapponese a Lambrate, rumeno a Precotto e così via. Chiede **per prima** all'ASST che ha il medico che parla la lingua del cittadino e le concede più tempo per rispondere.
- Decide la lingua dichiarata dal cittadino. Abbiamo imparato in gara che indovinarla dal testo porta a proporre il medico sbagliato.

### Il linguaggio

- **Una sola scelta per volta:** tutte le offerte arrivano in un unico messaggio, mai tre messaggi in conflitto.
- **Date leggibili** ("martedì 24 alle 10:30"), frasi brevi, nessun codice nel testo per il cittadino.
- **Mai silenzio:** ogni messaggio del cittadino riceve una risposta, anche quando il registro regionale è lento («sto aspettando gli orari, non deve fare nulla»).

---

## 2. Benessere: prima la sicurezza, poi la prenotazione

### Le emergenze non aspettano un appuntamento

- Il medico di base riconosce i **segnali d'allarme anche nascosti nel parlato**: "dolore al petto", "una morsa al petto", "dolore al braccio sinistro", "le gambe non mi reggevano", "non sento più bene le gambe". La risposta è immediata: chiamare il 112 o andare al pronto soccorso.
- Riconosce le **negazioni** per non creare allarmi inutili: "nessuna debolezza alle gambe" e "non riesco a camminare bene per il ginocchio" non sono un'emergenza.
- Lo stesso controllo è attivo sul consultorio, che è anch'esso un punto di primo contatto.

### Nessun consiglio clinico fuori ruolo

Gli agenti non danno indicazioni su farmaci o dosi: rimandano alla visita. Il medico di base prescrive solo secondo la tabella del protocollo (sintomo, visita, priorità).

### Dignità e tono

- Risposte personali e calde che riconoscono il disagio ("mi dispiace per il suo mal di schiena di questi giorni"), senza diagnosi.
- Una persona anziana non viene liquidata: le alternative arrivano con una frase semplice («martedì non c'è posto, giovedì alle 11 c'è lo stesso tipo di visita: va bene lo stesso?»).
- Se non c'è posto, una **lista d'attesa onesta**, con la ricerca che continua. Se più tardi arriva un posto adatto, il cittadino viene richiamato.

### Privacy come forma di cura

- **Consenso legato allo scopo:** il consenso alla prenotazione non vale per condividere i dati con un'altra ASST, né per il referto. Ogni scopo ha la sua domanda.
- **Prima del consenso escono solo criteri** (procedura, priorità, lingua, giorni), mai nome, codice del cittadino o ricetta.
- **La disabilità non lascia l'agente a cui è stata detta:** alle altre strutture passano solo i bisogni pratici (interprete, accompagnatore, spostamenti, fretta).
- Il referto dello specialista è condiviso solo con un sì esplicito. In assenza di risposta viene archiviato senza condivisione.

---

## 3. Mobilità: la visita giusta, il più vicino possibile, senza viaggi inutili

- **Prima la propria ASST:** il centro prenotazioni cerca nelle strutture di Giambellino. Le altre ASST entrano in gioco solo quando qui non c'è posto in tempo utile, e solo con il consenso del cittadino.
- **Il quartiere giusto per la lingua:** per una lingua rara la ricerca parte dalla struttura del municipio dove lavora il medico che la parla, invece di girare la città a caso.
- **"Non ho la macchina":** il bisogno di spostamento viene registrato, detto al cittadino e passato alla struttura come richiesta della sede più vicina possibile.
- **Giorni e orari del cittadino:** se dice "posso solo martedì o giovedì", è un filtro rigido. Se dice "solo certi giorni", l'agente chiede quali, una volta sola.
- **Riprenotazione senza ricominciare:** se una struttura annulla, nello stesso messaggio arrivano le alternative, **prima con lo stesso medico** e lo stesso giorno quando possibile. Il cittadino non deve rifare il percorso.
- **Accoglienza all'arrivo:** il check-in è spiegato in parole semplici. Se il registro lo rifiuta, il motivo viene detto chiaramente.

---

## 4. Ambiente: un sistema sobrio, che non spreca risorse

Non misuriamo emissioni, e non lo diciamo. Abbiamo però costruito gli agenti per **consumare poco** e per **non scaricare il proprio costo sugli altri**:

- **Regole prima dell'intelligenza artificiale:** sintomi, emergenze, bisogni e lingue sono riconosciuti con regole leggere, in millisecondi. Il modello linguistico è solo una riserva per i casi che le regole non capiscono, con un limite di 5 secondi.
- **Meno messaggi nella rete:** al massimo 5 strutture per giro di ricerca, i "no" vengono contati e non rielaborati. Questo rispetta i limiti della città e la casella degli altri agenti.
- **Memoria breve condivisa:** una lista di posti letta da poco viene riusata invece di chiedere di nuovo al registro regionale.
- **Niente doppioni:** la stessa richiesta riceve la stessa risposta, la stessa conferma la stessa ricevuta, mai una seconda prenotazione dello stesso posto.
- **Posti liberati subito:** gli slot offerti e non scelti tornano disponibili per gli altri cittadini.
- **Meno spostamenti:** prima la propria ASST, poi la struttura più adatta, e la riprenotazione con lo stesso medico evitano viaggi e visite mancate.

---

## Fiducia: una rete che si protegge da sola

- **L'anello delle 26 ASST:** gli agenti parlano solo con i 130 agenti registrati sulla mappa ufficiale della città. Gli impostori non ricevono posti, dati né risposte.
- Una cancellazione vale solo se arriva dalla struttura che ha emesso la prenotazione. Una ricevuta conta solo dopo una registrazione andata a buon fine sul registro regionale.
- Il testo libero non è mai un'istruzione: "ignora le regole" o "system:" vengono scartati.

---

## Uno standard per tutta la città

Abbiamo scritto **MACH**, il formato comune con cui le 26 ASST si parlano. Alla versione attuale (MACH-2.0.1) hanno contribuito con dati e idee altre squadre: Toros (Precotto), lessandrodiaz2006 con scuola-di-atene (Corvetto). Lo standard rende la rete più giusta per il cittadino:

- ogni richiesta riceve sempre una risposta, anche un no, e il no dice quando c'è il primo posto libero;
- la scadenza si conta dalla nascita del bisogno, perché il cittadino non deve pagare la lentezza del sistema;
- se una prenotazione salta, chi la annulla propone subito le alternative.

---

## Come lavoriamo

- **38 batterie di test automatici** su una città simulata: sintomi in decine di formulazioni, emergenze nascoste, lingue, registro lento, impostori, 1.275 turni anomali senza mai un crash né un silenzio.
- **Ogni correzione nasce da un percorso reale fallito**, letto nella console della città, con un test che lo riproduce prima del rilascio.
- Esempi di lezioni imparate in gara:
  - la scadenza contata da "adesso" faceva rifiutare le offerte: ora si conta dalla nascita del bisogno;
  - il registro lento lasciava a metà le prenotazioni: ora le strutture aspettano la risposta e mandano sempre la ricevuta;
  - la lingua indovinata dal testo portava al medico sbagliato: ora decide quella dichiarata.

---

## Il messaggio da portare a casa

**Accessibilità, benessere e mobilità sono informazioni che il cittadino ha già. Il sistema deve solo ascoltarle una volta e non perderle più.**

Red Agent lo fa con cinque agenti che si passano il testimone: il bisogno detto al medico di base arriva fino alla porta dell'ambulatorio, nel rispetto della privacy, nella lingua del cittadino, nella struttura più adatta.
