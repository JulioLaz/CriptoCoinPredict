import math
import time
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from arima import get_df_bitcoin,df_coin
from helpers import fig_to_base64

# ------------- TRATAMIENTO DE DATOS --------------#

def get_df_bitcoin_limpio(coin):
    start_time = time.time()

    df_data = get_df_bitcoin(coin)
    # df_data = df_coin(coin)
    df_bitcoin_limpio = df_data[["time", "close", "volumeto", "rsi", "macd", "macd_signal"]]
    df = df_bitcoin_limpio[df_bitcoin_limpio["volumeto"] != 0]
    duplicados = df.index.duplicated()
    df = df[~duplicados]
    df_bitcoin_limpio = df[df["close"] != 0]

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion get_df_bitcoin_limpio(coin): {duration:.2f} minutos")   

    return df_bitcoin_limpio

# ------------- ELIMINANDO OUTLIERS --------------#

def between_quartiles(coin):
    start_time = time.time()

    df = get_df_bitcoin_limpio(coin)
    cuartiles = [0, 0.25, 0.5, 0.75, 1]

    try:
        valores = df["close"].quantile(cuartiles)
    except ValueError:
        return None

    if math.isnan(valores[0.25]) or math.isnan(valores[0.75]):
        return None

    df_bitcoin_cuartiles = df.query(
        "close > " + str(int(valores[0.25])) + " & close < " + str(int(valores[0.75]))
    )
    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion between_quartiles(btc): {duration:.2f} minutos")    
    return df_bitcoin_cuartiles

# ------------- OBTENICIÓN DE DATOS COINMARKET--------------#

def extraer_tendencias(btc):
    start_time = time.time()

    global precio_actual, tendencia

    page = requests.get(f"https://www.coincarp.com/currencies/{btc}")
    soup = BeautifulSoup(page.content, "html.parser")
    precio = (soup.find("span", {"id": "coin-lastticker"}).text.strip().replace("$", "").replace(",", ""))
    precio_actual = float(precio)

    span_element = soup.find("div", {"class": ["cryptocurrencies-price d-flex align-items-center"]}).find("button")
    i_element = span_element.find("i")

    if "icon iconfont icon-solid-arrow-up" in i_element["class"]:
        tendencia = "alta"
    else:
        tendencia = "baja"

    porcentaje = span_element.text.strip().replace("$", "").replace(",", "")

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion extraer_tendencias(btc): {duration:.2f} minutos")

    return [precio_actual, tendencia, porcentaje]

# ------------- DESICIONES--------------#

def tomar_decisiones(coin, btc):
    start_time = time.time()
    
    global precio_actual, tendencia, media, rsi, macd, macd_signal, ma50, ma200,decision

    # df = between_quartiles(coin).tail(2000)
    # df=df_coin(coin)
    df=get_df_bitcoin_limpio(coin)
    print('get_df_bitcoin_limpio: ', df)

    if df is None:
        decision = "Sin datos"
        explicacion = "Explicación: No hay suficientes datos para tomar una decisión clara y asertiva. Los datos RSI, MACD y SiGNAL no cubren lo suficiente. Se recomienda buscar otra moneda o esperar a que haya más datos disponibles."
        return f"La decisión para este caso es: {decision}.\n\n{explicacion}"

    last_time=df['time'][-1:].values[0]
   

    df = df[["close", "volumeto", "rsi", "macd", "macd_signal"]]  # ordenamos columnas

    # Último RSI
    rsi = int(df.iat[-1, 2])
    # Últimol MACD
    macd = int(df.iat[-1, 3])
    # Último MACD-SIGNAL
    macd_signal = int(df.iat[-1, 4])

    # Calcular la media móvil de 50 días y 200 días
    df["ma50"] = df["close"].rolling(50).mean()
    df["ma200"] = df["close"].rolling(200).mean()

    ma50 = df["ma50"].iloc[-1]
    ma200 = df["ma200"].iloc[-1]

    # Precio actual
    Close = extraer_tendencias(btc)[0]
    precio = extraer_tendencias(btc)[0]
    # Tendencia actual
    tendencia = extraer_tendencias(btc)[1]
    # media
    media = int(df["close"].mean())

    # Definir umbrales para tomar decisiones
    rsi_sobrecompra = 62
    rsi_sobreventa = 38
    # Aplicar el criterio de decisión

    # if (
    #     precio > media
    #     and rsi > 50
    #     and macd > macd_signal
    #     and precio > ma50
    #     and precio > ma200
    # ):
    #     decision = "Comprar"
    #     explicacion = "Explicación: El precio actual está por encima de la media, el RSI es alto, el MACD está por encima de su señal,\n el precio actual está por encima de la MA50 y la MA200, lo que indica una tendencia alcista fuerte y una buena oportunidad para comprar."
    # elif (
    #     precio < media
    #     and rsi < 50
    #     and macd < macd_signal
    #     and precio < ma50
    #     and precio < ma200
    # ):
    #     decision = "Vender"
    #     explicacion = "Explicación: El precio actual está por debajo de la media, el RSI es bajo, el MACD está por debajo de su señal,\n el precio actual está por debajo de la MA50 y la MA200, lo que indica una tendencia bajista fuerte y una buena oportunidad para vender."
    # else:
    #     decision = "Mantener"

    #     if tendencia == "Alta":
    #         if precio > media and precio > ma50 and precio > ma200:
    #             explicacion = "Explicación: El precio actual está por encima de la media, la MA50 y la MA200, lo que indica una tendencia alcista. Aunque el RSI y el MACD no son muy altos, se recomienda mantener ya que la tendencia general es positiva y puede haber potencial para ganancias adicionales."

    #         elif precio < media and precio < ma50 and precio < ma200:
    #             explicacion = "Explicación: El precio actual está por debajo de la media, la MA50 y la MA200, lo que indica una tendencia bajista. Aunque el RSI y el MACD no son muy bajos, se recomienda mantener ya que la tendencia general es negativa y puede haber potencial para disminución adicional en las pérdidas."

    #         else:
    #             explicacion = "Explicación: Aunque la tendencia general es alcista, el precio actual no está lo suficientemente por encima de la media, la MA50 y la MA200 para justificar una compra adicional. Sin embargo, tampoco hay señales fuertes de venta, por lo que se recomienda mantener y seguir observando."

    #     elif tendencia == "Baja":
    #         if precio < media and precio < ma50 and precio < ma200:
    #             explicacion = "Explicación: El precio actual está por debajo de la media, la MA50 y la MA200, lo que indica una tendencia bajista. Aunque el RSI y el MACD no son muy bajos, se recomienda mantener ya que la tendencia general es negativa y puede haber potencial para disminución adicional en las pérdidas."

    #         elif precio > media and precio > ma50 and precio > ma200:
    #             explicacion = "Explicación: El precio actual está por encima de la media, la MA50 y la MA200, lo que indica una tendencia alcista. Aunque el RSI y el MACD no son muy altos, se recomienda mantener ya que la tendencia general es positiva y puede haber potencial para disminución adicional en las pérdidas."

    #     else:
    #         explicacion = "Explicación: Tendencia bajista pero precio no está lo suficientemente por debajo de media, MA50 y MA200 para justificar una venta adicional. Se recomienda mantener y observar."
    
    
    
    if Close > media and rsi > rsi_sobrecompra and macd > macd_signal and Close > ma50 and Close > ma200:
              if macd_signal < 0 and tendencia < 0:
                  decision = "Vender"
                  explicacion =f"Explicación: El precio actual ${Close} está por encima de la media ${media}, el RSI es alto: {rsi} (sobrecompra), el MACD ({macd}) es mayor al MACD_SIGNAL ({macd_signal}) está por encima de su señal y son menores a 0, la tendencia es en Baja, el precio actual está por encima de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia bajista y una buena oportunidad para VENDER."
              
              elif macd_signal < 0 and tendencia > 0:
                  decision = "Mantener"
                  explicacion =f"Explicación: Aunque el precio actual ${Close} está por encima de la media ${media}, el RSI es alto: {rsi} (sobrecompra), el MACD ({macd}) es mayor al MACD_SIGNAL ({macd_signal}) está por encima de su señal y son menores a 0, la tendencia es en Alta, el precio actual está por encima de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia alsista pero se recomineda ESPERAR."
        
    elif Close > media and rsi > 50 and macd > macd_signal and Close > ma50 and Close > ma200 and macd_signal < 0:
                  decision = "Mantener"
                  explicacion =f"Explicación: Aunque el precio actual ${Close} está por encima de la media ${media}, el RSI supera el nivel medio: {rsi} > 50, el MACD ({macd}) es mayor al MACD_SIGNAL ({macd_signal}) está por encima de su señal y son menores a 0, la tendencia es en {tendencia}, el precio actual está por encima de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia inestable por lo que se recomineda ESPERAR."

    elif Close > media and rsi > 50 and Close > ma50 and Close > ma200 and macd_signal > 0:
                  decision = "Mantener"
                  explicacion =f"Explicación: Aunque el precio actual ${Close} está por encima de la media ${media}, el RSI supera el nivel medio: {rsi} > 50, el MACD_SIGNAL ({macd_signal}) > 0, la tendencia es en {tendencia}, el precio actual está por encima de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia inestable por lo que se recomineda ESPERAR."

    elif Close < media and rsi < rsi_sobreventa and macd < macd_signal and Close < ma50 and Close < ma200:
              if macd_signal > 0 and tendencia > 0:
                  decision = "Comprar"
                  explicacion =f"Explicación: el precio actual ${Close} está por debajo de la media ${media}, el RSI es bajo: {rsi} (sobreventa), el MACD ({macd}) es menor al MACD_SIGNAL ({macd_signal}) está por debajo de su señal y son mayores a 0, la tendencia es en Alta, el precio actual está por debajo de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia alsista por lo que es una buena oportunidad para COMPRAR."

              elif macd_signal > 0 and tendencia < 0:
                  decision = "Mantener"
                  explicacion =f"Explicación: Aunque el precio actual ${Close} está por debajo de la media ${media}, el RSI es bajo: {rsi} (sobreventa), el MACD ({macd}) es menor al MACD_SIGNAL ({macd_signal}) está por debajo de su señal y son mayores a 0, la tendencia es en Baja, el precio actual está por debajo de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia inestable por lo que se recomineda ESPERAR."

    elif Close < media and rsi < 50 and macd < macd_signal and Close < ma50 and Close < ma200:
                  decision = "Mantener"
                  explicacion =f"Explicación: Aunque el precio actual ${Close} está por debajo de la media ${media}, el RSI esta por debajo del nivel medio: {rsi} < 50, el MACD ({macd}) es menor al MACD_SIGNAL ({macd_signal}) está por debajo de su señal y son mayores a 0, la tendencia es en {tendencia}, el precio actual está por debajo de la MA50: {ma50} y la MA200: {ma200}, lo que indica una tendencia inestable por lo que se recomineda ESPERAR."

    else:
                  decision = "Mantener"
                  explicacion= 'Los indicadores no proporcionan suficiente informacion para tomar una decisión, por lo que conviene seguir observando el movimiento y ESPERAR'

    end_time = time.time()
    duration = (end_time - start_time) / 60
    decision=decision.upper()

    print(f"Tiempo de ejecución funcion tomar_decisiones(coin, btc): {duration:.2f} minutos")

    return f"!!! {decision} !!!\n\nEsta es la decisión que conviene seguir en este caso. {explicacion}\n\nFecha/hora: {last_time}\n\nIndicadores:\nClose: ${Close}  -  Mean: ${media}\nMA50: ${ma50}  -  MA200: ${ma200}\nRSI: {rsi}  -  MACD: {macd}  -  MACD SIGNAL: {macd_signal}"


# ------------- GRAFICOS--------------#

def precios_medias(coin, btc):
    start_time=time.time()
    medias = None
    # Data Frame
    # data = df_coin(coin)
    data = get_df_bitcoin_limpio(coin)

    data.index = pd.to_datetime(data.index)

    if data.empty:
        return None

    # Calcular media:
    mean_price = data["close"].mean()

    # Desicion:
    result = tomar_decisiones(coin, btc)
    decision = result.split("! ")[1].split(" !")[0]
    decision=decision.upper()

    # decision = result.split(": ")[1].split(",")[0]

    # Calcular indicadores técnicos
    data["MA50"] = data["close"].rolling(window=50).mean()
    data["MA200"] = data["close"].rolling(window=200).mean()

    data = data.set_index("time")

    # Crear figura
    fig1, ax1 = plt.subplots(figsize=(8, 4))

    # Graficar los precios con las medias móviles
    data["close"].plot(ax=ax1, color="black", label="Precio", linewidth=0.7)
    data["MA50"].plot(ax=ax1, color="blue", label="Media Móvil de 50 días", linewidth=0.5)
    data["MA200"].plot(ax=ax1, color="red", label="Media Móvil de 200 días", linewidth=0.5)
    ax1.axhline(y=mean_price, color="green", linestyle="-", label="Precio Medio", linewidth=0.5)
    ax1.legend(loc="best", fontsize=9)
    # ax1.set_xlabel("Fecha")
    ax1.set_ylabel("Precio (USD)")
    ax1.set_title(f" Valor de cierre del {btc} con Medias Móviles")

    ax1.grid(axis='x', linestyle='--', alpha=0.7)
    ax1.xaxis.grid(True)

    ax1.set_xticklabels(ax1.get_xticklabels(), fontsize=7)
    # ax1.set_xticklabels(ax1.get_xticklabels(), rotation=10, fontsize=7)

    ax1.text(0.5,0.95,f"Decisión: {decision}",transform=ax1.transAxes,fontsize=16,color="red",verticalalignment="top",horizontalalignment="center",bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.5))

    medias = fig_to_base64(fig1)

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion precios_medias(coin, btc): {duration:.2f} minutos")
    
    return medias

def Close_about():
    interpretación= "Esta gráfica muestra el precio histórico de la cryto en color negro, junto con las medias móviles de 50 y 200 días en azul y rojo, respectivamente.\n La media móvil de 50 días se utiliza comúnmente como un indicador de tendencia a corto plazo, mientras que la media móvil de 200 días se utiliza como un indicador de tendencia a largo plazo."
    return interpretación


def rsi_tendencias(coin, btc):
    start_time=time.time()
    rsi = None

    # Data Frame
    df = get_df_bitcoin_limpio(coin)

    df = df[
        ["time", "close", "volumeto", "rsi", "macd", "macd_signal"]
    ]  # ordenamos columnas
    if df.empty:
        return "No hay suficientes datos(RSI)"

    df = df.set_index("time")

    # Calcular el RSI
    rsi = df.iat[-1, 2]

    # Calcular indicadores técnicos
    df["RSI"] = df["rsi"]

    # Crear figuras
    fig2, ax2 = plt.subplots(figsize=(8, 4))

    # Graficar el RSI
    df["RSI"].plot(
        ax=ax2, color="purple", label="Índice de Fuerza Relativa", linewidth=0.7
    )
    ax2.axhline(y=70,color="green",linestyle="--",label="Nivel de Sobrecompra: 70",linewidth=0.9)
    ax2.axhline(y=30,color="red",linestyle="--",label="Nivel de Sobreventa: 30",linewidth=0.9)
    ax2.legend(loc="best", fontsize=9)
    # ax2.set_xlabel("Fecha")
    ax2.set_ylabel("RSI")
    ax2.set_title("RSI")
    ax2.grid(axis='x', linestyle='--', alpha=0.7)
    ax2.xaxis.grid(True)
    ax2.set_xticklabels(ax2.get_xticklabels(), fontsize=7)
    # ax2.set_xticklabels(ax2.get_xticklabels(), rotation=10, fontsize=7)
    rsi = fig_to_base64(fig2)

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion rsi_tendencias(coin, btc): {duration:.2f} minutos")
    
    return rsi

def rsi_about():
      data="Interpretación: Esta gráfica muestra el Indice de Fuerza Relativa (RSI) en color morado. Los valores del RSI oscilan entre 0 y 100, y los niveles de sobrecompra y sobreventa se definen típicamente en 70 y 30, respectivamente. Cuando el RSI se acerca a los 30, se considera que la moneda está sobrevendida y podría aumentar en el futuro. Cuando el RSI se acerca a los 70, se considera que el precio está sobrecomprado y podría disminuir en el futuro."
      return data

def macd_tendencias(coin, btc):
    start_time=time.time()
    macd = None

    # Data Frame
    df = get_df_bitcoin_limpio(coin)
    df = df[
        ["time", "close", "volumeto", "rsi", "macd", "macd_signal"]
    ]  # ordenamos columnas
    if df.empty:
        return "No hay suficientes datos(MACD)"

    df = df.set_index("time")

    # Calcular el MACD
    macd = df.iat[-1, 3]

    # Calcular el MACD-SIGNAL
    macdsignal = df.iat[-1, 4]

    # Calcular indicadores técnicos
    df["MACD"] = df["macd"]
    df["M-Signal"] = df["macd_signal"]

    # Crear figuras
    fig3, ax3 = plt.subplots(figsize=(8, 4))

    # Graficar el MACD y la MACD-Señal
    df["MACD"].plot(ax=ax3,color="blue",label="MACD: Diferencia entre MA de 12 y 26 días",linewidth=0.7)
    df["M-Signal"].plot(ax=ax3, color="red", label="M-Signal: : MA de 9 días del MACD", linewidth=0.7)
    ax3.axhline(y=0, color="black", linestyle="--", linewidth=0.7)
    ax3.legend(loc="best", fontsize=9)
    # ax3.set_xlabel("Fecha")
    ax3.set_ylabel("MACD")
    ax3.set_title("MACD y Señal")

    ax3.grid(axis='x', linestyle='--', alpha=0.7)
    ax3.xaxis.grid(True)
    ax3.set_xticklabels(ax3.get_xticklabels(), fontsize=7)

    macd = fig_to_base64(fig3)
    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion macd_tendencias(coin, btc): {duration:.2f} minutos")
    return macd

def about_macd():
      data="El gráfico muestra el indicador MACD y su señal para el precio. El MACD es un indicador que se utiliza para identificar cambios en la tendencia y la fuerza de los movimientos de los precios. Se calcula a partir de la diferencia entre dos promedios móviles exponenciales de diferentes períodos. La línea de señal es una media móvil exponencial del MACD. Cuando la línea del MACD cruza por encima de la línea de señal, es una señal alcista, y cuando cruza por debajo, es una señal bajista."
      return data

def automatizar(coin, btc):
    start_time = time.time()

    get_df_bitcoin(coin)
    get_df_bitcoin_limpio(coin)
    between_quartiles(coin)
    extraer_tendencias(btc)
    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion automatizar(coin, btc): {duration:.2f} minutos")
    return automatizar
