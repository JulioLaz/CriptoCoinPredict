// Obtener reference a los canvas
const canvas1 = document.getElementById("grafico1");

// Obtener contextos de dibujo
const ctx1 = canvas1.getContext("2d");

// Cargar imagenes
let grafico1 = new Image();
grafico1.src = "data:image/png;base64, {{Grafico1}}";

// Dibujar cuando las imagenes carguen
grafico1.onload = function () {
  ctx1.drawImage(grafico1, 0, 0);
};
