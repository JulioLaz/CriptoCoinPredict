import datetime
import math
import time

import matplotlib.pyplot as plt
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup

from arima import get_df_bitcoin
from helpers import fig_to_base64

# ------------- OBTENICIÓN DE DATOS Y-FINANCE--------------#


def get_df_bitcoin_limpio(coin):
    df_data = get_df_bitcoin(coin)

    df_bitcoin_limpio = df_data[
        ["time", "close", "volumeto", "rsi", "macd", "macd_signal"]
    ]

    df = df_bitcoin_limpio[df_bitcoin_limpio["volumeto"] != 0]

    duplicados = df.index.duplicated()

    df = df[~duplicados]

    df_bitcoin_limpio = df[df["close"] != 0]

    return df_bitcoin_limpio


def between_quartiles(coin):
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

    return df_bitcoin_cuartiles


# ------------- OBTENICIÓN DE DATOS COINMARKET--------------#


def extraer_tendencias(btc):
    global precio_actual, tendencia

    time.sleep(5)

    page = requests.get(f"https://www.coincarp.com/currencies/{btc}")

    soup = BeautifulSoup(page.content, "html.parser")

    precio = (
        soup.find("span", {"id": "coin-lastticker"})
        .text.strip()
        .replace("$", "")
        .replace(",", "")
    )
    precio_actual = float(precio)

    span_element = soup.find(
        "div", {"class": ["cryptocurrencies-price d-flex align-items-center"]}
    ).find("button")
    i_element = span_element.find("i")
    if "icon iconfont icon-solid-arrow-up" in i_element["class"]:
        tendencia = "alta"
    else:
        tendencia = "baja"

    porcentaje = span_element.text.strip().replace("$", "").replace(",", "")

    return [precio_actual, tendencia, porcentaje]


# ------------- DESICIONES--------------#


def tomar_decisiones(coin, btc):
    global symbol, period, interval, df_bitcoin, precio_actual, tendencia, media, rsi, macd, macdsignal, ma50, ma200

    df = between_quartiles(coin)
    if df is None:
        decision = "Sin datos"
        explicacion = "Explicación: No hay suficientes datos para tomar una decisión clara y asertiva. Los datos RSI, MACD y SiGNAL no cubren lo suficiente. Se recomienda buscar otra moneda o esperar a que haya más datos disponibles."
        return f"La decisión para este caso es: {decision}, ya que su {explicacion}"

    df = df[["close", "volumeto", "rsi", "macd", "macd_signal"]]  # ordenamos columnas

    # Último RSI
    rsi = df.iat[-1, 2]
    # Últimol MACD
    macd = df.iat[-1, 3]
    # Último MACD-SIGNAL
    macdsignal = df.iat[-1, 4]

    # Calcular la media móvil de 50 días y 200 días
    df["ma50"] = df["close"].rolling(50).mean()
    df["ma200"] = df["close"].rolling(200).mean()

    ma50 = df["ma50"].iloc[-1]
    ma200 = df["ma200"].iloc[-1]

    # Precio actual
    precio = extraer_tendencias(btc)[0]
    # Tendencia actual
    tendencia = extraer_tendencias(btc)[1]
    # media
    media = df["close"].mean()

    # Aplicar el criterio de decisión

    if (
        precio > media
        and rsi > 50
        and macd > macdsignal
        and precio > ma50
        and precio > ma200
    ):
        decision = "Comprar"
        explicacion = "Explicación: El precio actual está por encima de la media, el RSI es alto, el MACD está por encima de su señal,\n el precio actual está por encima de la MA50 y la MA200, lo que indica una tendencia alcista fuerte y una buena oportunidad para comprar."
    elif (
        precio < media
        and rsi < 50
        and macd < macdsignal
        and precio < ma50
        and precio < ma200
    ):
        decision = "Vender"
        explicacion = "Explicación: El precio actual está por debajo de la media, el RSI es bajo, el MACD está por debajo de su señal,\n el precio actual está por debajo de la MA50 y la MA200, lo que indica una tendencia bajista fuerte y una buena oportunidad para vender."
    else:
        decision = "Mantener"

        if tendencia == "Alta":
            if precio > media and precio > ma50 and precio > ma200:
                explicacion = "Explicación: El precio actual está por encima de la media, la MA50 y la MA200, lo que indica una tendencia alcista. Aunque el RSI y el MACD no son muy altos, se recomienda mantener ya que la tendencia general es positiva y puede haber potencial para ganancias adicionales."

            elif precio < media and precio < ma50 and precio < ma200:
                explicacion = "Explicación: El precio actual está por debajo de la media, la MA50 y la MA200, lo que indica una tendencia bajista. Aunque el RSI y el MACD no son muy bajos, se recomienda mantener ya que la tendencia general es negativa y puede haber potencial para disminución adicional en las pérdidas."

            else:
                explicacion = "Explicación: Aunque la tendencia general es alcista, el precio actual no está lo suficientemente por encima de la media, la MA50 y la MA200 para justificar una compra adicional. Sin embargo, tampoco hay señales fuertes de venta, por lo que se recomienda mantener y seguir observando."

        elif tendencia == "Baja":
            if precio < media and precio < ma50 and precio < ma200:
                explicacion = "Explicación: El precio actual está por debajo de la media, la MA50 y la MA200, lo que indica una tendencia bajista. Aunque el RSI y el MACD no son muy bajos, se recomienda mantener ya que la tendencia general es negativa y puede haber potencial para disminución adicional en las pérdidas."

            elif precio > media and precio > ma50 and precio > ma200:
                explicacion = "Explicación: El precio actual está por encima de la media, la MA50 y la MA200, lo que indica una tendencia alcista. Aunque el RSI y el MACD no son muy altos, se recomienda mantener ya que la tendencia general es positiva y puede haber potencial para disminución adicional en las pérdidas."

        else:
            explicacion = "Explicación: Tendencia bajista pero precio no está lo suficientemente por debajo de media, MA50 y MA200 para justificar una venta adicional. Se recomienda mantener y observar."

    return f"La decisión para este caso es: {decision}, ya que su {explicacion}"


# ------------- GRAFICOS--------------#


def precios_medias(coin, btc):
    medias = None
    # Data Frame
    data = get_df_bitcoin_limpio(coin)
    if data.empty:
        return None

    # Calcular media:
    mean_price = data["close"].mean()

    # Desicion:
    result = tomar_decisiones(coin, btc)
    decision = result.split(": ")[1].split(",")[0]

    # Calcular indicadores técnicos
    data["MA50"] = data["close"].rolling(window=50).mean()
    data["MA200"] = data["close"].rolling(window=200).mean()

    data = data.set_index("time")

    # Crear figura
    fig1, ax1 = plt.subplots(figsize=(10, 4))

    # Graficar los precios con las medias móviles
    data["close"].plot(ax=ax1, color="black", label="Precio", linewidth=0.7)
    data["MA50"].plot(
        ax=ax1, color="blue", label="Media Móvil de 50 días", linewidth=0.5
    )
    data["MA200"].plot(
        ax=ax1, color="red", label="Media Móvil de 200 días", linewidth=0.5
    )
    ax1.axhline(
        y=mean_price, color="green", linestyle="-", label="Precio Medio", linewidth=0.5
    )
    ax1.legend(loc="best", fontsize=9)
    ax1.set_xlabel("Fecha")
    ax1.set_ylabel("Precio (USD)")
    ax1.set_title(f"{btc} Precios con Medias Móviles")

    # Texto explicativo de la grafica:
    text_price_medias_01 = f"Interpretación: Esta gráfica muestra el precio histórico de {btc} en color gris, junto con las medias móviles"
    text_price_medias_02 = "de 50 y 200 días en azul y rojo, respectivamente. "
    text_price_medias_03 = "La media móvil de 50 días se utiliza comúnmente como un indicador de tendencia a corto plazo, mientras que la media"
    text_price_medias_04 = (
        "móvil de 200 días se utiliza como un indicador de tendencia a largo plazo."
    )

    # Mostrar decision en grafico
    ax1.text(
        0.5,
        0.95,
        f"Decisión: {decision}",
        transform=ax1.transAxes,
        fontsize=20,
        color="red",
        verticalalignment="top",
        horizontalalignment="center",
        bbox=dict(boxstyle="round", facecolor="yellow", alpha=0.5),
    )

    ax1.text(
        0, -0.2, text_price_medias_01, transform=ax1.transAxes, fontsize=10, ha="left"
    )
    ax1.text(
        0, -0.25, text_price_medias_02, transform=ax1.transAxes, fontsize=10, ha="left"
    )
    ax1.text(
        0, -0.3, text_price_medias_03, transform=ax1.transAxes, fontsize=10, ha="left"
    )
    ax1.text(
        0, -0.35, text_price_medias_04, transform=ax1.transAxes, fontsize=10, ha="left"
    )

    medias = fig_to_base64(fig1)

    return medias


def rsi_tendencias(coin, btc):
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
    fig2, ax2 = plt.subplots(figsize=(10, 4))

    # Graficar el RSI
    df["RSI"].plot(
        ax=ax2, color="purple", label="Índice de Fuerza Relativa", linewidth=0.7
    )
    ax2.axhline(
        y=70,
        color="green",
        linestyle="--",
        label="Nivel de Sobrecompra: 70",
        linewidth=0.9,
    )
    ax2.axhline(
        y=30,
        color="red",
        linestyle="--",
        label="Nivel de Sobreventa: 30",
        linewidth=0.9,
    )
    ax2.legend(loc="best", fontsize=9)
    ax2.set_xlabel("Fecha")
    ax2.set_ylabel("RSI")
    ax2.set_title("RSI")

    # Texto explicativo de RSI:
    text_RSI_01 = f"Interpretación: Esta gráfica muestra el Indice de Fuerza Relativa (RSI) de {btc} en color morado. Los valores del RSI"
    text_RSI_02 = "oscilan entre 0 y 100, y los niveles de sobrecompra y sobreventa se definen típicamente en 70 y 30, respectivamente."
    text_RSI_03 = f"Cuando el RSI se acerca a los 30, se considera que el precio de {btc} está sobrevendido y podría aumentar en el futuro."
    text_RSI_04 = f"Cuando el RSI se acerca a los 70, se considera que el precio de {btc} está sobrecomprado y podría disminuir en el futuro."

    ax2.text(0, -0.20, text_RSI_01, transform=ax2.transAxes, fontsize=10, ha="left")
    ax2.text(0, -0.25, text_RSI_02, transform=ax2.transAxes, fontsize=10, ha="left")
    ax2.text(0, -0.3, text_RSI_03, transform=ax2.transAxes, fontsize=10, ha="left")
    ax2.text(0, -0.35, text_RSI_04, transform=ax2.transAxes, fontsize=10, ha="left")

    rsi = fig_to_base64(fig2)

    return rsi


def macd_tendencias(coin, btc):
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
    fig3, ax3 = plt.subplots(figsize=(10, 4))

    # Graficar el MACD y la MACD-Señal
    df["MACD"].plot(
        ax=ax3,
        color="blue",
        label="MACD: Diferencia entre MA de 12 y 26 días",
        linewidth=0.7,
    )
    df["M-Signal"].plot(
        ax=ax3, color="red", label="M-Signal: : MA de 9 días del MACD", linewidth=0.7
    )
    ax3.axhline(y=0, color="black", linestyle="--", linewidth=0.7)
    ax3.legend(loc="best", fontsize=9)
    ax3.set_xlabel("Fecha")
    ax3.set_ylabel("MACD")
    ax3.set_title("MACD y Señal")

    # Texto explicativo de MACD y la MACD-Señal:
    text_MACD_01 = f"El gráfico muestra el indicador MACD y su señal para el precio de {btc}. El MACD es un indicador que se utiliza para"
    text_MACD_02 = "identificar cambios en la tendencia y la fuerza de los movimientos de los precios. Se calcula a partir de la diferencia"
    text_MACD_03 = "entre dos promedios móviles exponenciales de diferentes periodos. La línea de señal es una media móvil exponencial del MACD."
    text_MACD_04 = "Cuando la línea del MACD cruza por encima de la línea de señal, es una señal alcista, y cuando cruza por debajo, es una señal bajista."

    # Agregar cuadro de texto debajo del gráfico
    ax3.text(
        0,
        -0.2,
        text_MACD_01,
        transform=ax3.transAxes,
        fontsize=10,
        ha="left",
        color="black",
    )
    ax3.text(
        0,
        -0.25,
        text_MACD_02,
        transform=ax3.transAxes,
        fontsize=10,
        ha="left",
        color="black",
    )
    ax3.text(
        0,
        -0.3,
        text_MACD_03,
        transform=ax3.transAxes,
        fontsize=10,
        ha="left",
        color="black",
    )

    macd = fig_to_base64(fig3)

    return macd


# ------------- BUSCAR RESPUESTA --------------#


def automatizar(coin, btc):
    get_df_bitcoin(coin)
    get_df_bitcoin_limpio(coin)
    between_quartiles(coin)
    extraer_tendencias(btc)

    return automatizar
