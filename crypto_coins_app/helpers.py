import base64
import csv
from io import BytesIO
import os
import matplotlib
import requests
from bs4 import BeautifulSoup
import time

matplotlib.use("Agg")

web = "https://www.coincarp.com/"
web_coin = "https://coinmarketcap.com/"

if not os.path.exists("models"):
    os.makedirs("models")


def models_crypto():
    global save_crypto

    save_crypto = "./models/crypto_data.csv"

    return save_crypto


models_crypto()


def fig_to_base64(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    return img_base64


def mayus(coin):
    coin = coin.replace(" ", "")
    coin = coin.upper()
    return coin


def extraer():
    page = requests.get(web_coin)

    soup = BeautifulSoup(page.content, "html.parser")

    # Extraer los datos de los elementos HTML
    imagenes = soup.find_all("img", class_="coin-logo")
    enlaces = soup.find_all("div", class_="sc-aef7b723-0 LCOyB")
    nombres = soup.find_all("p", class_="sc-4984dd93-0 kKpPOn")
    monedas = soup.find_all("p", class_="sc-4984dd93-0 iqdbQL coin-item-symbol")

    # Extraer los datos del dataframe de Python en un diccionario
    datos = {
        "imagen": [imagen["src"] for imagen in imagenes],
        "web_completa": [f'{web}{enlace.find("a")["href"]}' for enlace in enlaces],
        "moneda_nombre": [
            f'{moneda.text}\n{nombre.text}'
            for moneda, nombre in zip(monedas, nombres)
        ],
    }

    return datos


def extraer_icon_name():
    page = requests.get(web_coin)

    soup = BeautifulSoup(page.content, "html.parser")

    # Extraer los datos de los elementos HTML
    imagenes = soup.find_all("img", class_="coin-logo")
    # enlaces = soup.find_all("div", class_="sc-aef7b723-0 LCOyB")
    # nombres = soup.find_all("p", class_="sc-4984dd93-0 kKpPOn")
    monedas = soup.find_all("p", class_="sc-4984dd93-0 iqdbQL coin-item-symbol")

    # Extraer los datos del dataframe de Python en un diccionario
    datos = {
        "imagen": [imagen["src"] for imagen in imagenes],
        # "web_completa": [f'{web}{enlace.find("a")["href"]}' for enlace in enlaces],
        "moneda_nombre": [
            f'{moneda.text}' for moneda in monedas
        ],
    }

    return datos


def generar_html(datos):
    html = ""
    for i in range(len(datos["imagen"])):
        html += f"""
        <a href="{datos['web_completa'][i]}">
          <img src="{datos['imagen'][i]}" />
          <p>{datos['moneda_nombre'][i]}</p>
        </a>
    """
    return html

# def generar_coin_icons_siglas(datos):
#     icons = ""

#     for i in range(len(datos["imagen"])):
#         icons += f"""
#         <div class="coin-container">
#           <img style='width: 5rem;' src="{datos['imagen'][i]}" />
#           <p class="p_coin">{datos['moneda_nombre'][i]}</p>
#         </div>
#     """
#     return icons

def generar_coin_icons_siglas(datos):
    global crypto_nombre
    icons = ""

    for i in range(len(datos["imagen"])):
        crypto_nombre = datos['moneda_nombre'][i].split('\n')[0]  # Obtén el nombre de la criptomoneda
        print('crypto_nombre:',crypto_nombre)
        icons += f"""
        <div class="julio" data-crypto-name="{crypto_nombre}">
          <div class="coin-container julio">
            <img style='width: 5rem;' src="{datos['imagen'][i]}" />
            <p class="p_coin">{datos['moneda_nombre'][i]}</p>
          </div>
        </div>
        """
    return icons



def get_crypto_data():
    all_names = []
    all_links = []

    page = 1
    while True:
        # print(f'Processing page {page}')

        response = requests.get(f"{web}pn_{page}.html")
        soup = BeautifulSoup(response.text, "html.parser")

        for span in soup.find_all("span", class_="symbo"):
            text = ""

            for child in span.children:
                if child.name != "i":
                    text += child.strip()

            if text:
                all_names.append(text)

        links = soup.find_all("td", class_="td2 sticky")

        for link in links:
            a_tag = link.find("a")
            href = a_tag["href"]
            if href not in all_links:
                all_links.append(href)

        if page > 19:
            break

        time.sleep(5)

        page += 1

    cleaned_links = []
    for link in all_links:
        link = link.replace("/currencies/", "")
        link = link.rstrip("/")
        cleaned_links.append(link)

    name_to_link = {}
    for name, link in zip(all_names, cleaned_links):
        name_to_link[name] = link

    return name_to_link


def get_crypto_info(coin):
    name_to_link = get_crypto_data()

    # Guardar el diccionario en CSV
    with open("./models/crypto_data.csv", "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        for name, link in name_to_link.items():
            writer.writerow([name, link])

    # Leer CSV
    with open(save_crypto, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if coin in row:
                return row[1]
    return None
