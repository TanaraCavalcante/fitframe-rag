# Come scrivere contenuti per la knowledge base

Questo documento spiega come funziona la cartella `knowledge_base/` e come
scrivere un nuovo articolo — è una guida per chi mantiene i contenuti, non
un documento di pianificazione tecnica (quello è
[docs/plans/plan-fitframe-rag.md](plans/plan-fitframe-rag.md)).

## Come vengono usati questi file

1. All'avvio di `api.py`, `rag.py` legge **tutti** i file `.md` dentro
   `knowledge_base/` (funzione `carica_base_conoscenza`).
2. Ogni file viene diviso in chunk di testo (`crea_vector_store`) e
   trasformato in un vettore numerico (embedding) con un modello locale —
   nessuna registrazione manuale necessaria, basta che il file esista nella
   cartella al momento dell'avvio.
3. Quando un utente fa una domanda nel gestionale, il servizio cerca il
   chunk più simile alla domanda (FAISS) e lo manda come contesto al
   modello Groq, che scrive la risposta finale.
4. Se **riavvii** il servizio (`python api.py`), l'indice viene
   ricostruito da zero leggendo lo stato attuale dei file — quindi per far
   apparire un nuovo articolo (o una modifica a uno esistente) basta
   riavviare il processo, senza nessun altro passaggio.

## Come scrivere un nuovo file

- **Un file per argomento**, nome in kebab-case che descrive la domanda a
  cui risponde, es. `come-modifico-il-hero.md`, `come-aggiungo-un-corso.md`.
- **Titolo con `#`** in cima, che ripete la domanda a cui l'articolo
  risponde (es. `# Come modifico il Hero della pagina?`).
- **Contenuto in italiano**, passo per passo, con lo stesso linguaggio ed
  etichette che l'utente vede davvero nell'interfaccia del gestionale (nomi
  di menu, nomi di campo, nomi di pulsanti) — non parafrasare le etichette,
  copiale esattamente da lì.
- **Verifica sempre nel codice di FitFrame** (controller, form request,
  vista Blade) quali sono i vincoli reali (campi obbligatori/facoltativi,
  formati di file accettati, limiti di dimensione) prima di scriverli
  nell'articolo — non indovinare né generalizzare da altre funzionalità
  simili. Un'informazione sbagliata qui produce una risposta sbagliata
  dell'assistente.
- Se una funzionalità ha più sezioni o modalità (es. il Hero ha una
  modalità "immagini" e una "video", mutuamente esclusive), descrivile
  entrambe chiaramente, così il modello ha il contesto per rispondere a
  domande su ciascuna.

## Cosa il modello NON deve fare

Il `SYSTEM_PROMPT` in `api.py` istruisce il modello a non inventare mai
risposte che non sono presenti nel contesto recuperato — se un articolo è
incompleto o mancante, il modello risponde onestamente che non ha trovato
l'informazione e rimanda all'assistenza tecnica, invece di indovinare.
Questo significa che un articolo scritto in modo impreciso o incompleto è
peggio di nessun articolo: meglio scrivere poche informazioni ma corrette,
ed estendere l'articolo in un secondo momento.
