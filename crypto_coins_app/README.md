# CryptoPrediciones
Cripto Predicción: Decisión y predicción de valor futuro de criptomonedas:

* @author: Lazarte, Julio
* @author: Maldonado , William
* @author: San Martín , Luis

![Imagen del app funcionando](img/img.png)

## Description
Es un proyecto de Data Science (motivado por el #ElProfeAlejo en el bootcamp que cursamos actuamente octubre/2023) con el cual se debe obtener una decisíon de compra/venta/espera respecto del BTC-USD con los datos de 'Close' y de la tendencia y su gráfica correspondiente. Para eso se obtienen los valores de la criptomoneda desde yahoo finance (o mediante api de https://www.coincarp.com) y también la tendencia con web scraping, se realiza el tratamiento de datos y luego mediante un algoritmmo de decisión se logra el resultado. Para mejorar dicha decisión recurrimos a otros indicadores como: RSI, MA50, MA200, MACD Y MACD_SIGNAL. Además incorporamos un un método predictivo usando modelo ARIMA. Pero para ampliar el umbral del BTC decidimos hacerlos también para otras criptomonedas. El trabajo anterior fue realizado en google colab, que luego lo convertimos en una app.py para ejecutarlo y realizar su posterior deploy.