import os
import time
import pickle
import matplotlib.pyplot as plt
import pandas as pd
import requests
import ta
from statsmodels.tsa.arima.model import ARIMA
from helpers import fig_to_base64
API_KEY = os.getenv("API_KEY")
from dotenv import load_dotenv
import os

load_dotenv()

port = os.getenv("port")
secret_key = os.getenv("SECRET_KEY")

def models():
    start_time = time.time()

    global save_modelo
    save_modelo = "./models/modelo_arima.pkl"
    end_time = time.time()
    duration = (end_time - start_time) / 60  # duración en minutos
    print(f"Tiempo de ejecución funcion models(): {duration:.2f} minutos")
    return save_modelo
models()

def df_coin(coin):


    start_time = time.time()
    global indice_lista_close, close_lista_close
    API_KEY = os.getenv("API_KEY")
    

    symbol = coin
    period = 1000
    interval = 1  #minutos
    exchange = "USD"

    url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym={exchange}&aggregate={interval}&limit={period}&api_key={API_KEY}"
    response = requests.get(url)

    data = response.json()
    df = pd.DataFrame(data["Data"]["Data"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize("UTC")
    df = df.set_index("time")
    df.index = df.index.strftime('%Y-%m-%d %H:%M')
    df_btc_close = df["close"]

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion df_coin(): {duration:.2f} minutos")

    return df_btc_close

def predecir(coin):

    start_time = time.time()
    global indice_lista_close, close_lista_close

    symbol = coin
    period = 1000
    interval = 1  #minutos
    exchange = "USD"

    url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={symbol}&tsym={exchange}&aggregate={interval}&limit={period}&api_key={API_KEY}"
    response = requests.get(url)

    data = response.json()
    df = pd.DataFrame(data["Data"]["Data"])
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize("UTC")
    df = df.set_index("time")

# ---------------------------------------------
# !!!!!!!!!!!!!!!!!!!!!!nuevo!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    duplicados = df.index.duplicated()
    df = df[~duplicados]
    df = df[df["close"] != 0]
# ---------------------------------------------
    df_btc_close = df["close"]

    # model_pkl = ARIMA(df_btc_close, order=(1, 1, 1))
    model_pkl = ARIMA(df_btc_close, order=(3, 3, 3))
    results = model_pkl.fit()


    # ruta_modelo = "/content/drive/MyDrive/MODELOS_ENTRENADOS/modelo_arima_1_1_1.pkl"
    ruta_modelo = "./models/modelo_arima.pkl"

    # Guardar el modelo y los resultados en un archivo
    with open(ruta_modelo, "wb") as archivo_modelo:
        pickle.dump({"model": model_pkl, "results": results}, archivo_modelo)
    
    """# Realizar predicciones"""
    # Realizar predicciones
    forecast_steps = 5  # Por ejemplo, pronosticar 10 pasos en el futuro

    df_last_close = df["close"].tail(forecast_steps)
    df_last_close = pd.DataFrame(df_last_close)

    # Realiza las predicciones
    forecast = results.get_forecast(steps=forecast_steps)

    # Extraer las predicciones y los intervalos de confianza
    forecasted_values = forecast.predicted_mean
    # confidence_intervals = forecast.conf_int()

    df_predicciones=pd.DataFrame(forecasted_values)

    # Crear una lista con el índice del DataFrame
    df_last_close.index = df_last_close.index.strftime('%Y-%m-%d %H:%M')
    # df_last_close.index = df_last_close.index.strftime('%Y-%m-%d %H:%M:%S')
    indice_lista_close = df_last_close.index.tolist()

    # Crear una lista con los valores de la columna "close"
    df_last_close['close'] = df_last_close['close'].round(2)
    close_lista_close = df_last_close['close'].tolist()

    # Crear una lista con los valores de la columna "predicted_mean"
    df_predicciones['predicted_mean'] = df_predicciones['predicted_mean'].round().astype(int)
    predicted_mean = df_predicciones['predicted_mean'].tolist()

    # Crear una lista con el índice del DataFrame
    df_predicciones.index = df_predicciones.index.strftime('%Y-%m-%d %H:%M')
    # df_predicciones.index = df_predicciones.index.strftime('%Y-%m-%d %H:%M:%S')
    indice_lista = df_predicciones.index.tolist()

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion predecir(): {duration:.2f} minutos")

    return list(zip(indice_lista, predicted_mean))

def last_close_table():
       return list(zip(indice_lista_close, close_lista_close))


def grafico_predecir(coin):
    start_time = time.time()

    symbol = coin
    period = 1000
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
    # df["time"] = df["time"].dt.strftime('%Y-%m-%d')

    df = df.set_index("time")
    df_btc_close = df["close"]

    # Cargar el modelo y los resultados
    with open(save_modelo, "rb") as archivo_modelo:
        modelo_y_resultados = pickle.load(archivo_modelo)

    # Recuperar el modelo y los resultados del diccionario
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

    # Graficar las predicciones y los datos originales
    ultimas_horas = 100
    fig4 = plt.figure(figsize=(8, 4))
    ax4 = fig4.add_subplot(111)
    ax4.plot(df_btc_close.tail(ultimas_horas), label="Datos Originales", color="blue")
    ax4.plot(forecast_dates, forecasted_values, label="Predicciones", color="red")
    ax4.fill_between(forecast_dates,confidence_intervals.iloc[:, 0],confidence_intervals.iloc[:, 1], color="red",alpha=0.3,label="Intervalo de Confianza" )

    ax4.legend(loc='upper left', ncol=1)
    ax4.set_title(f"Predicciones de {coin}-USD con ARIMA por hora" ,fontsize=18)
    ax4.grid(axis='x', linestyle='--', alpha=0.7)
    ax4.xaxis.grid(True)
    ax4.set_xticklabels(ax4.get_xticklabels(), rotation=20, fontsize=7)


    ax4.grid(True,axis='x')
    prediccion = fig_to_base64(fig4)

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion last_close_table(): {duration:.2f} minutos")
       
    return prediccion

def arima_about():
    data=f"En la gráfica se observa una línea azul representando las últimas 500 hs, y una linea roja de predicción con su intervalo de confianza difuminado. Es una representación visual de cómo el modelo ARIMA predice el comportamiento futuro de una serie temporal. Cuanto más ajustadas estén las predicciones al intervalo de confianza, mayor será la confianza en el modelo."
    return data

def get_df_bitcoin(coin):

    start_time = time.time()
    symbol = coin
    period = 1000
    # period = 2000
    interval = 1
    exchange = "USD"

    url = f"https://min-api.cryptocompare.com/data/v2/histominute?fsym={symbol}&tsym={exchange}&aggregate={interval}&limit={period}&api_key={API_KEY}"

    response = requests.get(url)

    data = response.json()

    df = pd.DataFrame(data["Data"]["Data"])

    df["time"] = pd.to_datetime(df["time"], unit="s")
    df["time"] = df["time"].dt.tz_localize("UTC")
    # df = df.set_index("time")
    # df.index = df.index.strftime('%Y-%m-%d %H:%M')
    # df_btc_close = df["close"]
    # Formatee el valor de la columna `time` en el formato `"%Y-%m-%d %H:%M"`.
    df["time"] = df["time"].dt.strftime('%Y-%m-%d %H:%M')
    # df["time"] = df["time"].dt.strftime('%H:%M')
    df["close"] = df["close"].astype(int)

    df = df[["time", "high", "low", "open", "volumefrom", "volumeto", "close"]]

    df_bitcoin = pd.DataFrame(df)

    # Calcular indicadores
    df_bitcoin["rsi"] = (ta.momentum.RSIIndicator(df_bitcoin["close"]).rsi()).round(0)
    df_bitcoin["macd"] = (ta.trend.MACD(df_bitcoin["close"]).macd()).round(0)
    df_bitcoin["macd_signal"] = (ta.trend.MACD(df_bitcoin["close"]).macd_signal()).round(0)

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion get_df_bitcoin(): {duration:.2f} minutos")

    return df_bitcoin
