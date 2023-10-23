import os
from dotenv import load_dotenv
from flask import Flask, flash, render_template, request
from arima import grafico_predecir, models, predecir
from helpers import extraer, generar_html, get_crypto_info, mayus, models_crypto
from utils import (
    automatizar,
    macd_tendencias,
    precios_medias,
    rsi_tendencias,
    tomar_decisiones,
)

load_dotenv()

port = os.getenv("port")
secret_key = os.getenv("SECRET_KEY")

app = Flask(__name__, template_folder="templates")
app.secret_key = secret_key


# @app.before_first_request
def load_models():
    models()
    models_crypto()


@app.route("/")
def home():
    # Generar el HTML en el div class= "coin" html
    html = generar_html(extraer())

    # Renderizar la plantilla HTML
    return render_template("index.html", html=html)


@app.route("/respond", methods=["GET", "POST"])
def respuesta_chatbot():
    html = generar_html(extraer())
    # pregunta = next(request.form.values())
    coin_html = request.form["coin"]
    # crypto_html = request.form["crypto"]

    coin = mayus(coin_html)
    # crypto = get_crypto_info(coin)

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
    predicion = predecir(coin)
    grafico1 = precios_medias(coin, crypto)
    if grafico1 is None:
        flash("No hay suficientes datos para generar el gráfico 1.")
    grafico2 = rsi_tendencias(coin, crypto)
    grafico3 = macd_tendencias(coin, crypto)
    grafico4 = grafico_predecir(coin)

    return render_template(
        "index.html",
        html=html,
        Desicion=respuesta,
        Predipcion=predicion,
        Grafico1=grafico1,
        Grafico2=grafico2,
        Grafico3=grafico3,
        Grafico4=grafico4,
    )


if __name__ == "__main__":
    load_models()
    app.run(host="0.0.0.0", port=port)
