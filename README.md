# fitframe-rag

Servizio Python di RAG (Retrieval-Augmented Generation) che risponde in
italiano alle domande sull'uso del gestionale FitFrame, a partire da una
base di conoscenza scritta a mano in Markdown.

**Stack:** Flask · Groq (`openai/gpt-oss-120b`) · FAISS · embeddings
HuggingFace locali (`paraphrase-multilingual-MiniLM-L12-v2`)

---

## Architettura

Questo servizio fa parte di un sistema a due repository:

| Repository | Ruolo |
|---|---|
| **fitframe-rag** *(questo)* | Pipeline RAG completa + API Flask, stateless |
| **FitFrame** | Laravel — autenticazione, rotta `backend/chat`, persistenza cronologia, widget frontend |

Il contratto tra i due è minimo: Laravel manda `{ "domanda": "..." }`,
questo servizio risponde `{ "risposta": "..." }`. Nessuna cronologia,
nessun accesso a filesystem o database condiviso. Dettagli delle decisioni
architetturali in [docs/plan-fitframe-rag.md](docs/plan-fitframe-rag.md).

---

## Setup

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Se `Activate.ps1` viene bloccato dalla policy di esecuzione:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**macOS / Linux:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crea il file `.env` (puoi copiare `.env.example`):
```
GROQ_API_KEY=la_tua_chiave
```
Chiave disponibile su [console.groq.com/keys](https://console.groq.com/keys).

---

## Avviare il servizio

```bash
python api.py
# server su http://127.0.0.1:5002
```

Alla partenza il servizio legge tutti i file `.md` in `knowledge_base/` e
costruisce l'indice FAISS in memoria (nessuna cache su disco: l'indice è
sempre coerente con i file più recenti). Se `knowledge_base/` è vuota,
il servizio parte comunque e `/ask` risponde con un messaggio di assenza
di informazioni.

Per fermare: `Ctrl+C`, oppure su Windows in background:
```powershell
netstat -ano | findstr :5002
Stop-Process -Id <PID>
```

---

## Endpoint API

### `GET /health`
```json
{ "status": "ok", "chunks": 12 }
```

### `POST /ask`
**Body:**
```json
{ "domanda": "Come aggiungo un prodotto?" }
```

**Risposta (200):**
```json
{ "risposta": "Vai nella sezione Prodotti e clicca su Nuovo prodotto..." }
```

**Errori:**
- `400` — domanda mancante o vuota
- `503` — errore interno nel motore RAG (es. Groq non raggiungibile)

---

## Base di conoscenza

I contenuti vivono in `knowledge_base/*.md`, un file per argomento, in
italiano. È il posto dove aggiungere nuove domande/risposte sul
funzionamento del gestionale — nessun passaggio aggiuntivo di
build/registrazione richiesto, basta aggiungere il file e riavviare il
servizio.

---

## Test

```bash
pytest
```

I test dell'API mockano la chiamata a Groq (nessuna chiave richiesta per
eseguirli); i test della pipeline RAG usano il contenuto reale di
`knowledge_base/`.

---

## Struttura del progetto

```
api.py                       — API Flask, endpoint /ask e /health
rag.py                        — pipeline RAG (carica .md → chunk → embed → cerca)
knowledge_base/               — contenuti Markdown della base di conoscenza
tests/                        — suite pytest
requirements.txt
.env.example
docs/plan-fitframe-rag.md     — piano e decisioni architetturali
```
