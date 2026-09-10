# api.py
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from groq import Groq

from rag import carica_base_conoscenza, cerca_contesto, crea_vector_store

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "knowledge_base")
GROQ_MODEL = "openai/gpt-oss-120b"

MESSAGGIO_NON_TROVATO = (
    "Non ho trovato questa informazione nella documentazione del gestionale. "
    "Per maggiori informazioni contatta l'assistenza tecnica."
)

SYSTEM_PROMPT = (
    "Sei l'assistente di aiuto del gestionale FitFrame. Rispondi sempre in "
    "italiano, in modo chiaro e diretto, basandoti esclusivamente sul "
    "contesto fornito. Non inventare mai risposte che non sono presenti nel "
    f"contesto. Se il contesto non contiene la risposta, rispondi "
    f"esattamente: '{MESSAGGIO_NON_TROVATO}'"
)

documenti = carica_base_conoscenza(KNOWLEDGE_BASE_DIR)
vector_store, n_chunks = crea_vector_store(documenti)

if vector_store is None:
    logger.warning(
        "Nessun file .md trovato in %s: /ask risponderà sempre con "
        "messaggio di assenza di informazioni.",
        KNOWLEDGE_BASE_DIR,
    )
else:
    logger.info("Base di conoscenza indicizzata: %d chunk.", n_chunks)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "chunks": n_chunks})


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    domanda = (data.get("domanda") or "").strip()

    if not domanda:
        return jsonify({"error": "Domanda vuota"}), 400

    if vector_store is None:
        return jsonify({"risposta": MESSAGGIO_NON_TROVATO})

    try:
        contesto, _ = cerca_contesto(vector_store, domanda)

        risposta_groq = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Contesto:\n---\n{contesto}\n---\n\nDomanda: {domanda}",
                },
            ],
        )
        risposta = risposta_groq.choices[0].message.content
    except Exception:
        logger.exception("Errore durante la generazione della risposta")
        return jsonify({"error": "Assistente temporaneamente non disponibile"}), 503

    return jsonify({"risposta": risposta})


if __name__ == "__main__":
    app.run(port=5002, debug=False)
