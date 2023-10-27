from sklearn.preprocessing import StandardScaler
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from helpers import fig_to_base64


def rForestRegr():
# Función para calcular el RSI
   bitcoin = yf.Ticker("BTC-USD")
   data = bitcoin.history(period="100d", interval='1h')

   def calculate_RSI(data, window=14):
      delta = data.diff(1)
      gain = delta.where(delta > 0, 0)
      loss = -delta.where(delta < 0, 0)
      avg_gain = gain.rolling(window=window).mean()
      avg_loss = loss.rolling(window=window).mean()
      rs = avg_gain / avg_loss
      rsi = 100 - (100 / (1 + rs))
      return rsi

   # Función para calcular el MACD
   def calculate_MACD(data, short_window=12, long_window=26, signal_window=9):
      short_ema = data.ewm(span=short_window, adjust=False).mean()
      long_ema = data.ewm(span=long_window, adjust=False).mean()
      macd = short_ema - long_ema
      signal_line = macd.ewm(span=signal_window, adjust=False).mean()
      return macd, signal_line

   # Función para estimar valores futuros con regresión polinómica de grado n
   def estimate_future_value(data, col_name):
      X = np.arange(len(data)).reshape(-1, 1)
      y = data[col_name]

      # Ajusta una regresión polinómica de grado n
      grado = 4
      poly = PolynomialFeatures(degree=grado)
      X_poly = poly.fit_transform(X)
      poly_reg = LinearRegression()
      poly_reg.fit(X_poly, y)

      # Estima el valor en el siguiente punto
      future_value = poly_reg.predict(poly.fit_transform(np.array([[len(data)]])))
      return future_value

   # Obtén datos de Bitcoin

   # ... Cálculo de características y preparación de datos ...

   # Calcula las características (variables independientes)
   data['Price_Volume_Ratio'] = data.apply(lambda row: 0 if row['Volume'] == 0 else row['Close'] / row['Volume'], axis=1)
   data['RSI'] = calculate_RSI(data['Close'], 14)
   data['MA_50'] = data['Close'].rolling(window=50).mean()
   data['MA_200'] = data['Close'].rolling(window=200).mean()

   macd, signal_line = calculate_MACD(data['Close'], 12, 26, 9)
   data['MACD'] = macd
   data['Signal_Line'] = signal_line

   # Elimina filas con valores faltantes
   data.dropna(inplace=True)

   # Define las variables independientes (X) y la variable dependiente (y)
   X = data[['Price_Volume_Ratio', 'RSI', 'MA_50', 'MA_200', 'MACD']]
   y = data['Close']

   # Divide los datos en conjuntos de entrenamiento y prueba
   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

   # Escala los datos de entrenamiento
   scaler = StandardScaler()
   X_train_scaled = scaler.fit_transform(X_train)
   X_test_scaled = scaler.transform(X_test)

   # Entrena un modelo de regresión (Random Forest)
   # Define los hiperparámetros óptimos encontrados por GridSearchCV
   n_estimators = 200
   max_depth = 20
   min_samples_split = 2
   min_samples_leaf = 1

   # Crea un nuevo modelo con los hiperparámetros óptimos
   best_model = RandomForestRegressor(
      n_estimators=n_estimators,
      max_depth=max_depth,
      min_samples_split=min_samples_split,
      min_samples_leaf=min_samples_leaf,
      random_state=42  # Asegúrate de usar el mismo random_state
   )

   best_model.fit(X_train_scaled, y_train)

   # Estima valores futuros para cada variable independiente
   # Copia el último dato como punto de partida
   future_data = data.iloc[-1:].copy()

   # Crea un rango de fechas futuras con intervalos de 1 hora
   periods = 2 
   hours_interval = 1 #intervalos de horas a predecir
   future_dates = pd.date_range(start=future_data.index[0], periods=periods, freq=f'{hours_interval}H')

   future_data = pd.DataFrame(index=future_dates, columns=X.columns)

   # Estima valores futuros para cada variable independiente
   for col in X.columns:
      future_values = []
      for date in future_dates:
         future_value = estimate_future_value(data.loc[data.index <= date], col)
         future_values.append(future_value[0])
      future_data[col] = future_values

   # Crea un nuevo DataFrame con las mismas columnas que el original, incluyendo las estimaciones
   future_data_extended = data.copy()
   # future_data_extended = future_data_extended.append(future_data)
   future_data_extended = pd.concat([future_data_extended, future_data])

   # Estándariza los datos futuros
   future_data_scaled = scaler.transform(future_data)
   future_data_extended_scaled = np.vstack([X_test_scaled[-1], future_data_scaled])

   # Realiza predicciones utilizando el modelo entrenado y los valores futuros extendidos
   predictions = best_model.predict(future_data_extended_scaled)

   # Ultimos datos predichos:

   ultimos_n_valores = predictions[-(periods):]
   # para reemplazar el primer valor predicho que corresponde a la última fecha cargada
   # y lograr continuidad en la gráfica:
   ultimos_n_valores[0] = data['Close'][-1:].values[0]

   ultimos_n_fechas = future_data_extended.index[-(periods):]

   mean_close = data['Close'].mean()

   n_dias_graf = 30
   plt.figure(figsize=(8, 4))
   plt.grid(axis='x', linestyle='--', alpha=0.7)

   plt.plot(data.index[-n_dias_graf:], data['Close'][-n_dias_graf:], label='Precio Real', linewidth=0.7, color='blue')
   plt.plot(ultimos_n_fechas, ultimos_n_valores, label='Predicciones', linewidth=0.7, color='red')

   date_format = mdates.DateFormatter('%Y-%m-%d %H:%M hs')
   plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))  # Intervalo de 2 horas
   plt.gca().xaxis.set_major_formatter(date_format)
   plt.axhline(y=mean_close, linewidth=0.7, color='purple', linestyle='--', label="Valor promedio")
   plt.title('Predicciones del Precio de Bitcoin: próxima hora futura')

   pred = ultimos_n_valores[1]
   ultimo_valor = data['Close'][-1:].values[0]
   delta = abs(pred - ultimo_valor)
   # print('delta de predict/ultimoValor: ', delta)

   plt.text(data.index[-2:-1].values[0], pred+50, f'${pred:.0f} predic', fontsize=10, ha='center', va='bottom', color='red')
   plt.text(data.index[-2:-1].values[0], data['Close'][-1:]-500, f'${ultimo_valor:.0f} valor real', fontsize=10, ha='center', va='bottom', color='blue', label="Ultimo valor real")

   plt.text(data.index[-1:].values[0], mean_close, f'${mean_close:.0f} mean', fontsize=9, ha='center', va='bottom', color='purple')

   plt.scatter(ultimos_n_fechas[-1], predictions[-1], s=20, c='red', marker='o', label='Último Valor Predicho')
   plt.scatter(data.index[-1:].values[0], data['Close'][-1:], s=20, c='blue', marker='o', label='Último Valor Close')

   plt.xlabel('Fecha')
   plt.xticks(rotation=45)
   plt.gca().xaxis.set_tick_params(labelsize=7)
   plt.ylabel('Precio de Bitcoin')
   plt.legend()
   plt.grid(axis='x', linestyle='--', alpha=0.7)

   rForestRegr = fig_to_base64(plt)

   return rForestRegr

def about_RFR():
   data='Predicción utilizando Random Forest Regressor y PolynomialFeatures combinado a LinearRegression. R. Forest es un algoritmo de aprendizaje automático ampliamente utilizado en tareas de regresión. Se basa en el concepto de "bosques aleatorios" , que combina múltiples árboles de decisión para realizar predicciones'
   return data