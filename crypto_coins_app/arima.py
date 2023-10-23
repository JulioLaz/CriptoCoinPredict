import os
import pickle
import time
import matplotlib.pyplot as plt
import pandas as pd
import requests
import ta
from statsmodels.tsa.arima.model import ARIMA

from helpers import fig_to_base64

API_KEY = os.getenv("API_KEY")


def models():
    global save_modelo

    save_modelo = "./models/modelo_arima.pkl"

    return save_modelo


models()


def predecir(coin):
    symbol = coin
    period = 2000
    interval = 1
    exchange = "USD"

    url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym={exchange}&aggregate={interval}&limit={period}&api_key={API_KEY}"
    response = requests.get(url)

    data = response.json()
    df = pd.DataFrame(data["Data"]["Data"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize("UTC")
    df = df.set_index("time")
    df_btc_close = df["close"]

    model_pkl = ARIMA(df_btc_close, order=(3, 3, 3))
    results = model_pkl.fit()

    ruta_modelo = "./models/modelo_arima.pkl"

    # Guardar el modelo y los resultados en un archivo
    with open(ruta_modelo, "wb") as archivo_modelo:
        pickle.dump({"model": model_pkl, "results": results}, archivo_modelo)

    """#Extraccion del Modelo de la raiz:"""

    # Cargar el modelo y los resultados
    with open(save_modelo, "rb") as archivo_modelo:
        modelo_y_resultados = pickle.load(archivo_modelo)

    # Recuperar el modelo y los resultados del diccionario
    model_cargado = modelo_y_resultados["model"]
    results = modelo_y_resultados["results"]

    """# Realizar predicciones"""

    df_last_close = df["close"].tail(3)
    df_last_close = pd.DataFrame(df_last_close)

    # Realizar predicciones
    forecast_steps = 25  # Por ejemplo, pronosticar 10 pasos en el futuro

    # Realiza las predicciones
    forecast = results.get_forecast(steps=forecast_steps)

    # Extraer las predicciones y los intervalos de confianza
    forecasted_values = forecast.predicted_mean
    confidence_intervals = forecast.conf_int()

    df_predicciones = pd.DataFrame(forecasted_values)

    return f"Ultimos datos de Close {df_last_close}\n Predicciones {df_predicciones}"


def grafico_predecir(coin):
    # predicion = None

    start_time = time.time()

    symbol = coin
    period = 2000
    interval = 1
    exchange = "USD"

    url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym={exchange}&aggregate={interval}&limit={period}&api_key={API_KEY}"
    response = requests.get(url)

    data = response.json()
    if "Response" in data and data["Response"] == "Error":
        return "Validando datos..."

    df = pd.DataFrame(data["Data"]["Data"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize("UTC")
    df = df.set_index("time")
    df_btc_close = df["close"]

    # Cargar el modelo y los resultados
    with open(save_modelo, "rb") as archivo_modelo:
        modelo_y_resultados = pickle.load(archivo_modelo)

    # Recuperar el modelo y los resultados del diccionario
    model_cargado = modelo_y_resultados["model"]
    results = modelo_y_resultados["results"]

    # Graficar las predicciones y los datos originales
    df_btc_close = df["close"]

    # Realizar predicciones
    forecast_steps = 5  # Por ejemplo, pronosticar 10 pasos en el futuro
    forecast = results.get_forecast(steps=forecast_steps)

    # Extraer las predicciones y los intervalos de confianza
    forecasted_values = forecast.predicted_mean
    confidence_intervals = forecast.conf_int()

    # Crear forecast_dates y ajustar las etiquetas
    last_date = df_btc_close.index[-1]
    forecast_dates = pd.date_range(start=last_date, periods=forecast_steps, freq="H")
    date_labels = [date.strftime("%H:%M") for date in forecast_dates]

    # Graficar las predicciones y los datos originales
    ultimas_horas = 100
    fig4 = plt.figure(figsize=(10, 4))
    ax4 = fig4.add_subplot(111)
    ax4.plot(df_btc_close.tail(ultimas_horas), label="Datos Originales", color="blue")
    ax4.plot(forecast_dates, forecasted_values, label="Predicciones", color="red")
    ax4.fill_between(
        confidence_intervals.index,
        confidence_intervals.iloc[:, 0],
        confidence_intervals.iloc[:, 1],
        color="red",
        alpha=0.3,
        label="Intervalo de Confianza",
    )

    ax4.legend()
    ax4.set_title(f"Predicciones de {coin}-USD con ARIMA por hora")

    predicion = fig_to_base64(fig4)

    end_time = time.time()
    duration = (end_time - start_time) / 60  # duración en minutos
    print(f"Tiempo de ejecución: {duration:.2f} minutos")

    return predicion


def get_df_bitcoin(coin):
    symbol = coin
    period = 2000
    interval = 5
    exchange = "USD"

    url = f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={symbol}&tsym={exchange}&aggregate={interval}&limit={period}&api_key={API_KEY}"

    response = requests.get(url)

    data = response.json()

    df = pd.DataFrame(data["Data"]["Data"])

    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize("UTC")

    # Formatee el valor de la columna `time` en el formato `"%Y-%m-%d %H:%M"`.
    df["time"] = df["time"].dt.strftime("%H:%M")

    df["close"] = df["close"].astype(int)

    df = df[["time", "high", "low", "open", "volumefrom", "volumeto", "close"]]

    df_bitcoin = pd.DataFrame(df)

    # Calcular indicadores
    df_bitcoin["rsi"] = (ta.momentum.RSIIndicator(df_bitcoin["close"]).rsi()).round(0)
    df_bitcoin["macd"] = (ta.trend.MACD(df_bitcoin["close"]).macd()).round(0)
    df_bitcoin["macd_signal"] = (
        ta.trend.MACD(df_bitcoin["close"]).macd_signal()
    ).round(0)

    return df_bitcoin
