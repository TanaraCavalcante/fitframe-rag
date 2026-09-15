from unittest.mock import MagicMock, patch

import api

AUTH_HEADERS = {"Authorization": f"Bearer {api.API_TOKEN}"}


def _crea_risposta_groq_fittizia(testo):
    risposta = MagicMock()
    risposta.choices = [MagicMock(message=MagicMock(content=testo))]
    return risposta


def test_health():
    client = api.app.test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_ask_senza_token_ritorna_401():
    client = api.app.test_client()
    resp = client.post("/ask", json={"domanda": "Come aggiungo un prodotto?"})
    assert resp.status_code == 401
    assert "error" in resp.get_json()


def test_ask_con_token_sbagliato_ritorna_401():
    client = api.app.test_client()
    resp = client.post(
        "/ask",
        json={"domanda": "Come aggiungo un prodotto?"},
        headers={"Authorization": "Bearer token-sbagliato"},
    )
    assert resp.status_code == 401
    assert "error" in resp.get_json()


def test_ask_domanda_vuota():
    client = api.app.test_client()
    resp = client.post("/ask", json={"domanda": "  "}, headers=AUTH_HEADERS)
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_ask_con_risposta_da_groq():
    client = api.app.test_client()

    with patch.object(
        api.client.chat.completions,
        "create",
        return_value=_crea_risposta_groq_fittizia("Vai in Prodotti e clicca Nuovo prodotto."),
    ):
        resp = client.post(
            "/ask", json={"domanda": "Come aggiungo un prodotto?"}, headers=AUTH_HEADERS
        )

    assert resp.status_code == 200
    assert resp.get_json()["risposta"] == "Vai in Prodotti e clicca Nuovo prodotto."


def test_ask_groq_non_disponibile_ritorna_503():
    client = api.app.test_client()

    with patch.object(
        api.client.chat.completions, "create", side_effect=RuntimeError("boom")
    ):
        resp = client.post(
            "/ask", json={"domanda": "Come aggiungo un prodotto?"}, headers=AUTH_HEADERS
        )

    assert resp.status_code == 503
    assert "error" in resp.get_json()
