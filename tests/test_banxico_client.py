
"""
Tests for the Banxico API client.
Pruebas para el cliente de la API de Banxico.
"""

import pandas as pd
import pytest

from banxico_client import fetch_exchange_rate_data


def test_missing_token_raises_error(monkeypatch):
    """Missing credentials must be rejected.
    Deben rechazarse las credenciales ausentes.
    """

    # Remove the environment variable for this test.
    # Eliminar la variable de entorno durante esta prueba.
    monkeypatch.delenv("BANXICO_TOKEN", raising=False)

    # No HTTP request should be necessary to detect a missing token.
    # No debe ser necesaria una solicitud HTTP para detectar la ausencia.
    with pytest.raises(ValueError, match="Missing Banxico API token"):
        fetch_exchange_rate_data("2026-01-01", "2026-01-31")


@pytest.mark.parametrize(
    "start_date,end_date",
    [
        ("2026/01/01", "2026-01-31"),
        ("2026-02-01", "2026-01-31"),
    ],
)
def test_invalid_date_ranges_raise_error(start_date, end_date):
    """Invalid dates and reversed ranges must be rejected.
    Deben rechazarse las fechas inválidas y los periodos invertidos.
    """

    with pytest.raises(ValueError):
        fetch_exchange_rate_data(
            start_date,
            end_date,
            token="test-token",
        )


def test_api_response_is_converted_to_standard_dataframe(monkeypatch):
    """API observations must use our standard column names.
    Las observaciones deben usar los nombres estándar del proyecto.
    """

    # Simulate the structure returned by the API.
    # Simular la estructura que devuelve la API.
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "bmx": {
                    "series": [
                        {
                            "datos": [
                                {"fecha": "05/01/2026", "dato": "17.95"},
                                {"fecha": "06/01/2026", "dato": "18.02"},
                            ]
                        }
                    ]
                }
            }

    # Replace requests.get with a local simulation.
    # Sustituir requests.get por una simulación local.
    def fake_get(url, headers, timeout):
        assert "/series/SF43718/datos/" in url
        assert headers["Bmx-Token"] == "test-token"
        assert timeout == 30
        return FakeResponse()

    monkeypatch.setattr("banxico_client.requests.get", fake_get)

    # Run the client without contacting Banxico.
    # Ejecutar el cliente sin conectarse a Banxico.
    result = fetch_exchange_rate_data(
        "2026-01-01",
        "2026-01-31",
        token="test-token",
    )

    # Verify column names, dates, and values.
    # Verificar nombres de columnas, fechas y valores.
    assert list(result.columns) == ["date", "exchange_rate"]
    assert result["date"].tolist() == ["2026-01-05", "2026-01-06"]
    assert result["exchange_rate"].tolist() == ["17.95", "18.02"]
    assert isinstance(result, pd.DataFrame)
