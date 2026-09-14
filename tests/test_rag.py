import os

from rag import carica_base_conoscenza, cerca_contesto, crea_vector_store

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")


def test_carica_base_conoscenza_legge_i_file_md():
    documenti = carica_base_conoscenza(KNOWLEDGE_BASE_DIR)
    assert len(documenti) >= 1


def test_carica_base_conoscenza_cartella_vuota(tmp_path):
    documenti = carica_base_conoscenza(str(tmp_path))
    assert documenti == []


def test_crea_vector_store_con_documenti_vuoti():
    vector_store, n_chunks = crea_vector_store([])
    assert vector_store is None
    assert n_chunks == 0


def test_pipeline_completa_trova_contesto_rilevante():
    documenti = carica_base_conoscenza(KNOWLEDGE_BASE_DIR)
    vector_store, n_chunks = crea_vector_store(documenti)

    assert vector_store is not None
    assert n_chunks > 0

    contesto, risultati = cerca_contesto(vector_store, "Come modifico il hero?")
    assert "hero" in contesto.lower()
    assert len(risultati) > 0
