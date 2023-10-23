from app import app
from utils import tomar_decisiones

coin = "BTC"
crypto = "bitcoin"

with app.test_client() as client:
    resp = client.post("/respond", data={"coin": coin, "crypto": crypto})
    print(resp.data)


respuesta = tomar_decisiones(coin, crypto)

print(respuesta)
