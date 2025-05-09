/**
 * Lógica JavaScript para el juego de ordenamiento interactivo.
 * Archivo: js/sortingGame.js
 */

// ==================== Variables de Estado del Juego ====================
let gameArray = [];                // Array lógico con los números a ordenar.
let gameElements = [];             // Array de referencias a los elementos DIV en el HTML.
let moves = 0;                     // Contador de movimientos del jugador.
let timerInterval = null;          // ID del intervalo del temporizador.
let seconds = 0;                   // Contador de segundos transcurridos.
let currentLevel = 1;              // Nivel actual del juego.
let firstSelectedElement = null;   // Almacena el primer elemento DOM clicado para un intercambio.
let firstSelectedIndex = -1;       // Índice del primer elemento seleccionado en gameElements/gameArray.
let isSwapping = false;            // Bandera para evitar clics mientras hay un intercambio en progreso.
let gameWon = false;               // Bandera para indicar si el juego actual ha sido ganado.

const MAX_LEVEL = 10; // Nivel máximo para evitar arrays demasiado grandes
const ELEMENTS_PER_LEVEL_INCREASE = 1; // Cuántos elementos añadir por nivel
const BASE_ELEMENTS = 4; // Elementos en el nivel 1 (BASE_ELEMENTS + (currentLevel-1)*INC) -> N1=4, N2=5

// ==================== Referencias a Elementos del DOM ====================
const gameArea = document.getElementById('game-area');
const moveCountSpan = document.getElementById('move-count');
const timerSpan = document.getElementById('timer');
const levelSpan = document.getElementById('level');
const startGameBtn = document.getElementById('start-game-btn');
const winMessageDiv = document.getElementById('win-message');

// ==================== Funciones Principales del Juego ====================

/**
 * Inicia o reinicia el juego para el nivel actual o el siguiente.
 */
function startGame() {
    console.log("Iniciando juego - Nivel:", currentLevel);
    gameWon = false;
    isSwapping = false;
    moves = 0;
    seconds = 0;
    firstSelectedElement = null;
    firstSelectedIndex = -1;

    winMessageDiv.style.display = 'none';
    winMessageDiv.classList.remove('visible'); // Por si se usa clase para animar
    startGameBtn.textContent = 'Reiniciar Juego'; // Cambiar texto del botón

    // Limpiar área de juego
    gameArea.innerHTML = '';
    gameElements = [];

    // Detener temporizador anterior
    stopTimer();

    // Generar array para el nivel
    const arraySize = BASE_ELEMENTS + (currentLevel - 1) * ELEMENTS_PER_LEVEL_INCREASE;
    gameArray = generateRandomArray(arraySize);

    // Renderizar elementos en el DOM
    renderGameArea();

    // Actualizar UI
    updateInfoDisplay();

    // Iniciar nuevo temporizador
    startTimer();
}

/**
 * Genera un array de números aleatorios únicos y desordenados.
 * @param {number} size - El tamaño del array a generar.
 * @returns {number[]} Un array de números desordenados.
 */
function generateRandomArray(size) {
    // Crear array ordenado de 1 a size
    const arr = Array.from({ length: size }, (_, i) => i + 1);

    // Mezclar el array (Algoritmo Fisher-Yates)
    for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]]; // Intercambio
    }
    console.log("Array generado:", arr);
    return arr;
}

/**
 * Crea y añade los elementos visuales (DIVs) al área de juego.
 * Cada DIV representa un número del gameArray.
 */
function renderGameArea() {
    gameArray.forEach((value) => {
        const element = document.createElement('div');
        element.classList.add('sort-element');
        element.textContent = value;
        element.dataset.value = value; // Almacena el valor numérico

        // --- Opcional: Estilo para BARRAS de altura variable ---
        // Si quieres barras, asegúrate que en `components.css` `.sort-element` NO tenga `height` fija.
        // Y descomenta las siguientes líneas:
        /*
        const maxHeight = 200; // Altura máxima de la barra en gameArea (ajusta según min-height de #game-area)
        const minHeight = 30;  // Altura mínima de la barra
        const heightPerUnit = (maxHeight - minHeight) / (gameArray.length > 1 ? Math.max(...gameArray) : 1); // Escala para la altura
        element.style.height = `${Math.max(minHeight, value * heightPerUnit)}px`;
        if (parseInt(element.style.height) < 40) { // Si la barra es muy pequeña para el texto
             element.style.fontSize = '0.8em';
             element.style.writingMode = 'vertical-rl'; // Opcional: texto vertical
             element.style.textOrientation = 'mixed';
        }
        */
        // --- Fin de sección para BARRAS ---

        element.addEventListener('click', handleElementClick);
        gameArea.appendChild(element);
        gameElements.push(element);
    });
    console.log("Elementos renderizados en el DOM.");
}

/**
 * Maneja el evento de clic en un elemento de ordenamiento.
 * Implementa la lógica de selección e intercambio de elementos adyacentes.
 * @param {MouseEvent} event - El evento de clic.
 */
function handleElementClick(event) {
    if (isSwapping || gameWon) return; // Ignorar clics si se está intercambiando o ya se ganó

    const clickedElement = event.currentTarget; // `currentTarget` es el elemento al que se añadió el listener
    const clickedIndex = gameElements.indexOf(clickedElement);

    if (firstSelectedElement === null) {
        // Primer clic: seleccionar el elemento
        firstSelectedElement = clickedElement;
        firstSelectedIndex = clickedIndex;
        clickedElement.classList.add('selected');
        console.log(`Elemento seleccionado: ${gameArray[firstSelectedIndex]} en índice ${firstSelectedIndex}`);
    } else {
        // Segundo clic
        if (firstSelectedElement === clickedElement) {
            // Clic en el mismo elemento: deseleccionar
            clickedElement.classList.remove('selected');
            firstSelectedElement = null;
            firstSelectedIndex = -1;
            console.log("Elemento deseleccionado.");
        } else {
            // Clic en un elemento diferente: intentar intercambiar si es adyacente
            console.log(`Intentando intercambiar con: ${gameArray[clickedIndex]} en índice ${clickedIndex}`);
            if (Math.abs(firstSelectedIndex - clickedIndex) === 1) {
                // Son adyacentes, proceder al intercambio
                isSwapping = true;
                firstSelectedElement.classList.remove('selected'); // Quitar 'selected' antes de animar 'swapping'

                // Añadir clase de 'swapping' para animación CSS
                firstSelectedElement.classList.add('swapping');
                clickedElement.classList.add('swapping');

                // Esperar un poco para que la animación de 'swapping' se vea antes del cambio de posición
                setTimeout(() => {
                    swapElements(firstSelectedIndex, clickedIndex); // Lógica y visual

                    // Quitar clase 'swapping' después de la transición de la posición
                    // El timeout debe ser similar o mayor a la duración de la transición CSS de 'transform' en .sort-element
                    setTimeout(() => {
                        // Es importante remover 'swapping' de los elementos correctos, que ahora podrían haber cambiado de lugar en gameElements
                        gameElements[firstSelectedIndex].classList.remove('swapping'); // El que originalmente era el segundo
                        gameElements[clickedIndex].classList.remove('swapping');     // El que originalmente era el primero

                        moves++;
                        updateInfoDisplay();
                        isSwapping = false;

                        if (isSorted()) {
                            gameOver();
                        }
                    }, 350); // Duración de la animación de 'swapping' y transición de movimiento
                }, 100); // Pequeña demora para que se aplique el estilo .swapping

            } else {
                // No son adyacentes: deseleccionar el primero y seleccionar el nuevo
                firstSelectedElement.classList.remove('selected');
                firstSelectedElement = clickedElement;
                firstSelectedIndex = clickedIndex;
                clickedElement.classList.add('selected');
                console.log(`No adyacentes. Nuevo elemento seleccionado: ${gameArray[firstSelectedIndex]}`);
            }
        }
    }
}


/**
 * Intercambia dos elementos en el array lógico (gameArray),
 * en el array de referencias DOM (gameElements), y visualmente en el DOM.
 * @param {number} index1 - Índice del primer elemento.
 * @param {number} index2 - Índice del segundo elemento.
 */
function swapElements(index1, index2) {
    console.log(`Intercambiando índices ${index1} (${gameArray[index1]}) y ${index2} (${gameArray[index2]})`);

    // 1. Intercambiar en el array lógico
    [gameArray[index1], gameArray[index2]] = [gameArray[index2], gameArray[index1]];

    // 2. Intercambiar en el array de referencias a elementos DOM
    [gameElements[index1], gameElements[index2]] = [gameElements[index2], gameElements[index1]];

    // 3. Intercambiar visualmente en el DOM
    // Esta es la parte más delicada. Asegurarse que el orden en `gameArea.children` coincida con `gameElements`.
    // Una forma es reconstruir el gameArea basado en el nuevo orden de gameElements.
    // O, si los elementos son hermanos directos y conocemos su orden, podemos usar insertBefore.
    const parent = gameArea;
    const elem1Node = gameElements[index1]; // El elemento que AHORA está en index1 (originalmente en index2)
    const elem2Node = gameElements[index2]; // El elemento que AHORA está en index2 (originalmente en index1)

    // Para reordenar correctamente en el DOM manteniendo la consistencia
    // la forma más segura es reconstruir o reinsertar en orden.
    // Temporalmente los quitamos para reinsertarlos en el orden de gameElements
    // Esta es una manera simple, puede causar un leve parpadeo. Una técnica más avanzada sería mover
    // solo los dos elementos implicados usando insertBefore de forma cuidadosa.

    // Forma sencilla y robusta de reordenar visualmente:
    gameElements.forEach(el => parent.appendChild(el)); // Re-añade todos en el nuevo orden

    // Resetear la selección para el próximo movimiento
    firstSelectedElement = null;
    firstSelectedIndex = -1;
}


/**
 * Comprueba si el array actual (gameArray) está ordenado de forma ascendente.
 * @returns {boolean} True si el array está ordenado, false en caso contrario.
 */
function isSorted() {
    for (let i = 0; i < gameArray.length - 1; i++) {
        if (gameArray[i] > gameArray[i + 1]) {
            return false;
        }
    }
    return true;
}

/**
 * Actualiza la visualización de movimientos, tiempo y nivel en el HTML.
 */
function updateInfoDisplay() {
    moveCountSpan.textContent = moves;
    timerSpan.textContent = `${seconds}s`;
    levelSpan.textContent = currentLevel;
}

/**
 * Inicia el temporizador del juego.
 */
function startTimer() {
    stopTimer(); // Asegurar que no haya múltiples intervalos
    seconds = 0; // Reiniciar segundos
    updateInfoDisplay(); // Mostrar 0s inmediatamente

    timerInterval = setInterval(() => {
        seconds++;
        timerSpan.textContent = `${seconds}s`; // Actualizar solo el tiempo aquí por eficiencia
    }, 1000);
}

/**
 * Detiene el temporizador.
 */
function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

/**
 * Maneja el fin del juego cuando la lista está ordenada.
 */
function gameOver() {
    console.log("¡Juego ganado!");
    gameWon = true;
    stopTimer();
    winMessageDiv.textContent = `¡Felicidades! Nivel ${currentLevel} completado en ${seconds}s con ${moves} movimientos.`;
    winMessageDiv.style.display = 'block';
    winMessageDiv.classList.add('visible'); // Para animaciones CSS

    saveScore(currentLevel, moves, seconds);

    if (currentLevel < MAX_LEVEL) {
        startGameBtn.textContent = 'Siguiente Nivel';
    } else {
        startGameBtn.textContent = 'Jugar de Nuevo (Nivel 1)';
        winMessageDiv.textContent += " ¡Has completado todos los niveles!";
    }
}

/**
 * Guarda la puntuación en localStorage.
 * @param {number} level
 * @param {number} moves
 * @param {number} time
 */
function saveScore(level, movesCount, timeInSeconds) {
    // Pedir nombre al jugador (opcional, podrías hacerlo siempre o si es un buen score)
    const playerName = prompt("¡Gran trabajo! Ingresa tu nombre para la tabla de puntuaciones:", "JugadorAnónimo");
    if (playerName === null || playerName.trim() === "") {
        // Si el usuario cancela o no ingresa nombre, no guardamos
        console.log("No se guardó la puntuación (nombre no ingresado).");
        return;
    }

    const scoreEntry = {
        name: playerName.trim(),
        level: level,
        moves: movesCount,
        time: timeInSeconds,
        date: new Date().toLocaleDateString('es-ES') // Formato de fecha local
    };

    try {
        const highscores = JSON.parse(localStorage.getItem('algorithmExplorerHighscores')) || [];
        highscores.push(scoreEntry);

        // Ordenar puntuaciones: por nivel (desc), luego movimientos (asc), luego tiempo (asc)
        highscores.sort((a, b) => {
            if (b.level !== a.level) {
                return b.level - a.level;
            }
            if (a.moves !== b.moves) {
                return a.moves - b.moves;
            }
            return a.time - b.time;
        });

        // Mantener solo las X mejores puntuaciones (ej. top 10)
        const MAX_SCORES_TO_KEEP = 10;
        const updatedHighscores = highscores.slice(0, MAX_SCORES_TO_KEEP);

        localStorage.setItem('algorithmExplorerHighscores', JSON.stringify(updatedHighscores));
        console.log("Puntuación guardada:", scoreEntry, "Top scores:", updatedHighscores);
    } catch (error) {
        console.error("Error al guardar la puntuación:", error);
    }
}


// ==================== Event Listeners ====================

startGameBtn.addEventListener('click', () => {
    if (gameWon) { // Si se ganó el juego anterior
        if (currentLevel < MAX_LEVEL) {
            currentLevel++;
        } else {
            currentLevel = 1; // Volver al nivel 1 si se completaron todos
        }
    }
    // Si no se había ganado (o se reinicia en medio de una partida) o es la primera vez,
    // simplemente inicia el juego con `currentLevel` (que ya fue ajustado si es post-victoria).
    startGame();
});

// ==================== Inicialización (al cargar la página) ====================
document.addEventListener('DOMContentLoaded', () => {
    // Podrías cargar el nivel desde localStorage si quieres persistencia entre sesiones
    // Por ahora, siempre empieza en nivel 1.
    levelSpan.textContent = currentLevel; // Mostrar nivel inicial
    startGameBtn.textContent = 'Iniciar Juego'; // Texto inicial del botón
    // Opcionalmente, llamar a startGame() aquí para que el juego inicie automáticamente:
    // startGame();
    // O esperar a que el usuario haga clic en el botón.
});