const boxes = document.querySelectorAll('.box_shadow');

// Escucha el evento de clic en cada elemento
boxes.forEach(box => {
  box.addEventListener('click', () => {
    const cryptoName = box.getAttribute('data-crypto-name'); // Obtiene el nombre de la criptomoneda
    const coinInput = document.querySelector('input[name="coin"]');
    coinInput.value = cryptoName; // Establece el valor del campo de entrada
    // Envía el formulario
    const form = document.querySelector('form');
    form.submit();
  });
});