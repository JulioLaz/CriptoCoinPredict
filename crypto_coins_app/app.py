import os
import time
from dotenv import load_dotenv
from flask import Flask, flash, render_template, request
from arima import grafico_predecir, models, predecir,last_close_table,arima_about
from helpers import extraer_img_coin,generar_coin_icons_target,extraer,extraer_icon_name, generar_html, get_crypto_info, mayus, models_crypto, generar_coin_icons_siglas
from utils import about_macd,Close_about,rsi_about,automatizar,macd_tendencias,precios_medias,rsi_tendencias,tomar_decisiones
from rForetsReg import rForestRegr,about_RFR

load_dotenv()

port = os.getenv("port")
secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__, template_folder="templates")
app.secret_key = secret_key
app.debug = True 

def load_models():
    models()
    models_crypto()

@app.route("/")
def home():
    global coin
    start_time = time.time()
    # Generar el HTML en el div class= "coin" html
    html = generar_html(extraer())
    icons = generar_coin_icons_siglas(extraer_icon_name())

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion home(): {duration:.2f} minutos")

    return render_template("index.html", html=html,icons=icons )



@app.route("/respond", methods=["GET", "POST"])
def respuesta_chatbot():
    start_time=time.time()
    global coin
    html = generar_html(extraer())
    icons = generar_coin_icons_siglas(extraer_icon_name())
    coin_html = request.form["coin"]

    # crypto_html = request.form["crypto"]

    coin = mayus(coin_html)
    extraer_img_coin(coin)
    target=generar_coin_icons_target(coin) #extraer_img_coin
    try:
        crypto = get_crypto_info(coin)
        if crypto is None:
            flash("La Crypto que elegiste no existe en Coincarp 😢")
            return render_template("index.html", html=html)
    except IndexError:
        flash("La Crypto que elegiste esta incorrecta y no existe en Coincarp ☠")
        return render_template("index.html", html=html)

    # automatizar(coin, crypto)

    try:
        automatizar(coin, crypto)
    except Exception as e:
        flash("Esta Crypto no existe en Cryptocompare 😂")
        return render_template("index.html", html=html)

    respuesta = tomar_decisiones(coin, crypto)
    prediccion = predecir(coin)
    lastClose = last_close_table()
    target=generar_coin_icons_target(coin) #extraer_img_coin
    aboutClose=Close_about()
    aboutArima=arima_about()
    aboutRsi=rsi_about()
    aboutMacd=about_macd()
    aboutRFR=about_RFR()

    grafico1 = precios_medias(coin, crypto)
    if grafico1 is None:
        flash("No hay suficientes datos para generar el gráfico 1.")
    grafico2 = rsi_tendencias(coin, crypto)
    grafico3 = macd_tendencias(coin, crypto)
    grafico4 = grafico_predecir(coin)
    grafico5 = rForestRegr()

    end_time = time.time()
    duration = (end_time - start_time) / 60
    print(f"Tiempo de ejecución funcion respuesta_chatbot(): {duration:.2f} minutos")

    return render_template(
        "index.html",
        html=html,
        Target=target,
        AboutClose=aboutClose,
        AboutArima=aboutArima,
        AboutRsi=aboutRsi,
        AboutMacd=aboutMacd,
        icons=icons,
        Desicion=respuesta,
        Prediccion=prediccion,
        LastClose = lastClose,
        Grafico1=grafico1,
        Grafico2=grafico2,
        Grafico3=grafico3,
        Grafico4=grafico4,
        Grafico5=grafico5,
        AboutRFR=aboutRFR,
    )


if __name__ == "__main__":
    load_models()
    app.run(host="0.0.0.0", port=port)
