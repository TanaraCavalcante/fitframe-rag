# rag.py
#
# Pipeline RAG: carica i file Markdown della base di conoscenza, costruisce
# l'indice FAISS e cerca il contesto più rilevante per una domanda.

import glob
import logging
import os

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def carica_base_conoscenza(cartella: str) -> list:
    """
    Carica tutti i file .md dentro `cartella` come lista di Document (LangChain).
    Restituisce una lista vuota se la cartella non esiste o non contiene
    nessun file .md (il chiamante decide come gestire una base vuota).
    """
    percorsi = sorted(glob.glob(os.path.join(cartella, "*.md")))

    documenti = []
    for percorso in percorsi:
        documenti.extend(TextLoader(percorso, encoding="utf-8").load())

    return documenti


def crea_vector_store(documenti: list, chunk_size: int = 800, chunk_overlap: int = 100):
    """
    Divide i documenti in chunk, calcola gli embedding localmente e indicizza
    tutto in FAISS. Restituisce (vector_store, n_chunks); vector_store è
    None se `documenti` è vuoto (nessun contenuto da indicizzare).
    """
    if not documenti:
        return None, 0

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documenti)

    modello_embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = FAISS.from_documents(chunks, modello_embeddings)

    return vector_store, len(chunks)


def cerca_contesto(vector_store, domanda: str, k: int = 4):
    """
    Cerca i k chunk più rilevanti per la domanda. Restituisce (contesto, risultati).
    """
    risultati = vector_store.similarity_search_with_score(domanda, k=k)

    testi = [doc.page_content for doc, score in risultati]
    contesto = "\n---\n".join(testi)

    return contesto, risultati
