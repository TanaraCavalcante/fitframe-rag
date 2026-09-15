# Piano: servizio RAG di aiuto contestuale (fitframe-rag)

Data: 2026-09-10
Stato: APPROVATO

## Contesto

Questo servizio Python risponde alle domande in linguaggio naturale sull'uso
del gestionale FitFrame (es. "Come aggiungo un prodotto?"), usando una base
di conoscenza scritta a mano in Markdown e recuperata tramite ricerca
semantica (RAG). Il lato Laravel (repository `FitFrame`,
`docs/plan-chatbot-rag-gestionale.md`) chiama questo servizio via HTTP e
persiste la cronologia; questo servizio è **stateless** e non ha accesso al
database di FitFrame.

Decisioni prese nella sessione FitFrame, non da ridiscutere qui:
- LLM: **Groq**, modello `openai/gpt-oss-120b`, tier gratuito.
- Embeddings: modello locale HuggingFace
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (no API
  esterna).
- Deploy: processo nativo (venv), non Docker.
- Contratto HTTP: Laravel manda `{ domanda }`, questo servizio risponde
  `{ risposta }`. Nessuna cronologia salvata qui.

## Decisioni prese in questa sessione

### Framework: Flask
Stesso framework di `ai-chat` (progetto gemello, stesso stack Groq+FAISS già
funzionante). Nessun motivo per introdurre FastAPI qui: il servizio ha un
solo endpoint reale, non serve validazione automatica avanzata né
documentazione OpenAPI generata.

### Porta: 5002
Confermata la proposta del piano FitFrame — `ai-chat` occupa già la 5001.

### Endpoint: `POST /ask`
- Richiesta: `{ "domanda": "..." }`
- Risposta (200): `{ "risposta": "..." }`
- Risposta (400): `{ "error": "..." }` — domanda mancante/vuota
- Risposta (503): `{ "error": "..." }` — errore nel motore RAG (es. Groq non
  raggiungibile, indice non pronto). Il lato Laravel gestisce già la
  mancata risposta del servizio (connessione rifiutata, timeout) come caso
  a parte; questo status serve per gli errori che avvengono *dopo* che la
  connessione HTTP è riuscita.

Tutti i messaggi restituiti dal servizio — inclusi quelli di errore
(`error`), non solo `risposta` — sono in italiano, coerente con la lingua
del gestionale.

Aggiunto anche `GET /health` → `{ "status": "ok", "chunks": N }`, utile per
verificare rapidamente che l'indice sia stato costruito (in locale o per un
futuro supervisor di processo).

### Autenticazione di `/ask`: token condiviso semplice
`/ask` richiede l'header `Authorization: Bearer <API_TOKEN>`: senza
token configurato, o con un token che non corrisponde, risponde `401`
senza elaborare la domanda (nessuna chiamata a Groq). Il valore di
`API_TOKEN` è una stringa casuale generata una volta e condivisa a mano
con il `.env` del progetto FitFrame (lì si chiama `RAG_SERVICE_TOKEN`) —
niente OAuth/JWT, il servizio ha un solo chiamante conosciuto. `/health`
resta pubblico, senza token: non fa query a Groq né espone dati sensibili.
Decisione arrivata da un confronto con la sessione FitFrame, che aveva
notato l'endpoint privo di qualunque controllo di provenienza.

### Base di conoscenza: `knowledge_base/*.md`
Cartella dedicata nella radice del repository, separata da `docs/` (che
resta per i documenti di pianificazione, come questo file). Un file
Markdown per argomento (es. `come-aggiungere-un-prodotto.md`), titolo con
`#` in cima. Contenuto **da scrivere/estendere nel tempo dall'utente** — in
questa sessione è stato creato solo un file di esempio per validare la
pipeline end-to-end.

### Indice FAISS: costruito all'avvio, non persistito su disco
Il corpus è piccolo e fisso (documentazione di poche pagine), quindi
ricostruire l'indice ad ogni avvio del processo è abbastanza veloce e
garantisce che l'indice sia sempre coerente con i file `.md` più recenti —
niente cache da invalidare manualmente. Se il corpus crescesse molto in
futuro, si può rivalutare la persistenza (`FAISS.save_local`).

### Gestione errori
- Cartella `knowledge_base/` vuota o inesistente → il servizio parte lo
  stesso (log di avviso), ma `/ask` risponde con un messaggio di cortesia
  ("nessuna informazione disponibile") invece di andare in errore.
- Eccezione durante la chiamata a Groq (rete, rate limit, chiave mancante)
  → catturata, loggata lato server, risposta 503 con messaggio generico in
  italiano — mai lo stack trace nella risposta HTTP.

## Struttura del progetto

```
api.py              — Flask, endpoint /ask e /health
rag.py              — pipeline RAG (carica .md → chunk → embed → cerca)
knowledge_base/      — contenuti Markdown della base di conoscenza
tests/               — pytest
requirements.txt
.env.example
README.md
docs/plans/plan-fitframe-rag.md   — questo file
```

## Punti in sospeso (non bloccanti per l'MVP)

- Scrivere il contenuto reale della base di conoscenza (oltre il file di
  esempio) — attività manuale dell'utente, fuori dallo scope del codice.
  Vedi [[fitframe-rag-content]].
- Nessun supervisor di processo su Windows: in sviluppo il servizio va
  avviato manualmente (`python api.py`); da rivalutare solo se il progetto
  arriva in produzione (coerente con la nota già presente nel piano
  FitFrame).

## Annotazioni integrate

> NOTA: la rag NON DEVE INVENTARE RISPOSTE, se non trova la risposta
> corrispondente alla domanda nei file, risponde onestamente che non sa la
> risposta e l'utente può entrare in contatto con l'assistenza tecnica per
> maggiori informazioni.

— **Integrata**: il `SYSTEM_PROMPT` in `api.py` già vietava di rispondere
oltre il contesto fornito, ma il messaggio di "non trovato" andava
aggiornato per includere il rimando all'assistenza tecnica. Nuovo testo:

> "Non ho trovato questa informazione nella documentazione del gestionale.
> Per maggiori informazioni contatta l'assistenza tecnica."

Applicato in `api.py` (`MESSAGGIO_NON_TROVATO`, riusato sia nel
`SYSTEM_PROMPT` che nella risposta quando la base di conoscenza è vuota).