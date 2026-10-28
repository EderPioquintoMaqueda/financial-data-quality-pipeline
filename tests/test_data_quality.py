
"""
Automated tests for financial data quality validation.
Pruebas automatizadas para validar la calidad de datos financieros.
"""

import pandas as pd
import pytest

# Import the function we want to test.
# Importar la función que queremos probar.
from data_quality import validate_exchange_rate_data


def test_valid_data_is_sorted():
    """
    Valid data must be sorted by date.
    Los datos válidos deben ordenarse por fecha.
    """

    # Create a DataFrame with dates intentionally out of order.
    # Crear una tabla con fechas intencionalmente desordenadas.
    df = pd.DataFrame({
        "date": ["2026-01-03", "2026-01-01"],
        "exchange_rate": [17.45, 17.38],
    })

    # Run the validation function.
    # Ejecutar la función de validación.
    result = validate_exchange_rate_data(df)

    # Confirm dates are in ascending order.
    # Confirmar que las fechas estén en orden ascendente.
    assert result["date"].is_monotonic_increasing

    # Confirm values follow the same date order.
    # Confirmar que los valores sigan el mismo orden de fechas.
    assert result["exchange_rate"].tolist() == [17.38, 17.45]


def test_missing_column_raises_error():
    """
    Missing required columns must be rejected.
    Deben rechazarse las columnas obligatorias ausentes.
    """

    # Create data without the exchange_rate column.
    # Crear datos sin la columna exchange_rate.
    df = pd.DataFrame({
        "date": ["2026-01-01"],
    })

    # Expect a ValueError with the message used by our function.
    # Esperar un ValueError con el mensaje que devuelve nuestra función.
    with pytest.raises(ValueError, match="Missing required columns"):
        validate_exchange_rate_data(df)


def test_invalid_date_raises_error():
    """
    Dates that cannot be interpreted must be rejected.
    Deben rechazarse las fechas que no se puedan interpretar.
    """

    # Provide an invalid date.
    # Proporcionar una fecha inválida.
    df = pd.DataFrame({
        "date": ["fecha-invalida"],
        "exchange_rate": [17.5],
    })

    # The function should reject the invalid date.
    # La función debe rechazar la fecha inválida.
    with pytest.raises(ValueError, match="Invalid or missing dates"):
        validate_exchange_rate_data(df)


def test_duplicate_dates_raise_error():
    """
    Duplicate dates must be rejected.
    Deben rechazarse las fechas duplicadas.
    """

    # Create two records with the same date.
    # Crear dos registros con la misma fecha.
    df = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-01"],
        "exchange_rate": [17.5, 17.6],
    })

    # The function should reject duplicate dates.
    # La función debe rechazar las fechas duplicadas.
    with pytest.raises(ValueError, match="Duplicate dates"):
        validate_exchange_rate_data(df)


@pytest.mark.parametrize(
    "invalid_rate",
    [
        None,           # Missing value / Valor ausente
        "texto",        # Non-numeric value / Valor no numérico
        0,              # Zero / Cero
        -1,             # Negative value / Valor negativo
        float("inf"),   # Positive infinity / Infinito positivo
        float("-inf"),  # Negative infinity / Infinito negativo
    ],
)
def test_invalid_exchange_rates_raise_error(invalid_rate):
    """
    Invalid exchange rates must be rejected.
    Deben rechazarse los tipos de cambio inválidos.
    """

    # Create a DataFrame with one invalid exchange rate.
    # Crear una tabla con un tipo de cambio inválido.
    df = pd.DataFrame({
        "date": ["2026-01-01"],
        "exchange_rate": [invalid_rate],
    })

    # Every invalid value should raise a ValueError.
    # Cada valor inválido debe generar un ValueError.
    with pytest.raises(ValueError):
        validate_exchange_rate_data(df)


def test_original_dataframe_is_unchanged():
    """
    Validation must not modify the original DataFrame.
    La validación no debe modificar la tabla original.
    """

    # Create data with dates out of order.
    # Crear datos con fechas desordenadas.
    df = pd.DataFrame({
        "date": ["2026-01-02", "2026-01-01"],
        "exchange_rate": [17.45, 17.38],
    })

    # Keep an independent copy of the original data.
    # Conservar una copia independiente de los datos originales.
    original = df.copy(deep=True)

    # Run validation.
    # Ejecutar la validación.
    validate_exchange_rate_data(df)

    # Verify that the original DataFrame has not changed.
    # Verificar que la tabla original no haya cambiado.
    pd.testing.assert_frame_equal(df, original)
