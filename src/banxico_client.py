
"""
Client for downloading financial time-series data from Banxico.
Cliente para descargar series de tiempo financieras de Banxico.
"""

import os
from datetime import datetime

import pandas as pd
import requests


# Base URL of the official Banxico SIE API.
# URL base de la API oficial del Sistema de Información Económica.
BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1"

# Series identifier for the FIX exchange rate, in pesos per US dollar.
# Identificador de la serie del tipo de cambio FIX, en pesos por dólar.
SERIES_ID = "SF43718"


def fetch_exchange_rate_data(
    start_date: str,
    end_date: str,
    token: str | None = None,
) -> pd.DataFrame:
    """
    Download exchange-rate observations from Banxico.
    Descargar observaciones del tipo de cambio desde Banxico.

    Args:
        start_date: First date, in YYYY-MM-DD format.
                    Fecha inicial, en formato YYYY-MM-DD.
        end_date: Last date, in YYYY-MM-DD format.
                  Fecha final, en formato YYYY-MM-DD.
        token: API access token. If omitted, read BANXICO_TOKEN
               from the environment.
               Token de acceso. Si se omite, leer BANXICO_TOKEN
               de las variables de entorno.

    Returns:
        A DataFrame with date and exchange_rate columns.
        Un DataFrame con las columnas date y exchange_rate.

    Raises:
        ValueError: If dates or token are invalid or missing.
        requests.RequestException: If the HTTP request fails.
        RuntimeError: If the API response has an unexpected structure.
    """

    # Use the provided token or read it from the environment.
    # Usar el token proporcionado o leerlo del entorno.
    token = token or os.getenv("BANXICO_TOKEN")

    # Stop before making a request if no token is available.
    # Detener el proceso si no hay un token disponible.
    if not token:
        raise ValueError(
            "Missing Banxico API token. Set BANXICO_TOKEN first."
        )

    # Parse the input strings into date objects.
    # Convertir las cadenas de entrada en objetos de fecha.
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(
            "Dates must use the YYYY-MM-DD format."
        ) from exc

    # The beginning of the requested period cannot be after its end.
    # El inicio del periodo no puede ser posterior a su final.
    if start > end:
        raise ValueError("start_date must be before or equal to end_date.")

    # Build the endpoint for the requested series and date range.
    # Construir la dirección de consulta para la serie y el periodo.
    url = (
        f"{BASE_URL}/series/{SERIES_ID}/datos/"
        f"{start_date}/{end_date}"
    )

    # Send the token in an HTTP header instead of the URL.
    # Enviar el token en una cabecera HTTP, no en la URL.
    headers = {"Bmx-Token": token}

    # Send the GET request and wait up to 30 seconds.
    # Enviar la solicitud GET y esperar hasta 30 segundos.
    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    # Raise an exception for HTTP errors such as 401 or 500.
    # Generar una excepción ante errores HTTP, como 401 o 500.
    response.raise_for_status()

    # Decode the JSON response into a Python dictionary.
    # Convertir la respuesta JSON en un diccionario de Python.
    payload = response.json()

    # Extract observations while detecting unexpected response formats.
    # Extraer observaciones y detectar estructuras inesperadas.
    try:
        observations = payload["bmx"]["series"][0]["datos"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "Unexpected response structure from Banxico API."
        ) from exc

    # Map the API's field names to our project's standard column names.
    # Adaptar los nombres de la API a las columnas estándar del proyecto.
    df = pd.DataFrame(
        observations,
        columns=["fecha", "dato"],
    ).rename(
        columns={
            "fecha": "date",
            "dato": "exchange_rate",
        }
    )

    # Banxico dates commonly arrive as day/month/year.
    # Las fechas de Banxico suelen llegar como día/mes/año.
    # Normalize them to YYYY-MM-DD to avoid ambiguous date parsing.
    # Normalizarlas a YYYY-MM-DD para evitar ambigüedades.
    parsed_dates = pd.to_datetime(
        df["date"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    df["date"] = parsed_dates.dt.strftime("%Y-%m-%d")

    # Return only the standardized columns.
    # Devolver únicamente las columnas estandarizadas.
    return df[["date", "exchange_rate"]]
