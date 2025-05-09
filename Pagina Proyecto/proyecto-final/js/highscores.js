/**
 * Lógica JavaScript para la página de Mejores Puntuaciones.
 * Archivo: js/highscores.js
 */

document.addEventListener('DOMContentLoaded', () => {
    const highscoresTableBody = document.getElementById('highscoresTableBody');
    const noScoresMessageDiv = document.getElementById('noScoresMessage');
    const clearScoresBtn = document.getElementById('clearScoresBtn');

    /**
     * Carga las puntuaciones desde localStorage.
     * @returns {Array} Un array de objetos de puntuación, o un array vacío.
     */
    function loadHighscores() {
        try {
            const scoresJSON = localStorage.getItem('algorithmExplorerHighscores');
            return scoresJSON ? JSON.parse(scoresJSON) : [];
        } catch (error) {
            console.error("Error al cargar las puntuaciones de localStorage:", error);
            return []; // Retornar array vacío en caso de error
        }
    }

    /**
     * Renderiza las puntuaciones en la tabla HTML.
     * @param {Array} scores - Array de objetos de puntuación.
     */
    function renderHighscores(scores) {
        // Limpiar contenido previo de la tabla
        highscoresTableBody.innerHTML = '';

        if (scores.length === 0) {
            noScoresMessageDiv.style.display = 'block'; // Mostrar mensaje de "sin puntuaciones"
            highscoresTableBody.closest('.scores-table-wrapper').style.display = 'none'; // Ocultar la tabla si está vacía
            if (clearScoresBtn) { // El botón podría no estar si no hay puntuaciones
                 clearScoresBtn.style.display = 'none'; // Ocultar botón de borrar si no hay nada que borrar
            }
            return;
        }

        noScoresMessageDiv.style.display = 'none'; // Ocultar mensaje
        highscoresTableBody.closest('.scores-table-wrapper').style.display = 'block'; // Mostrar tabla
         if (clearScoresBtn) {
            clearScoresBtn.style.display = 'inline-block'; // Asegurar que el botón sea visible
        }


        scores.forEach((score, index) => {
            const row = highscoresTableBody.insertRow();

            const rankCell = row.insertCell();
            rankCell.classList.add('rank');
            rankCell.textContent = index + 1;

            const nameCell = row.insertCell();
            nameCell.classList.add('player-name');
            nameCell.textContent = score.name || 'Jugador Anónimo'; // Fallback por si el nombre es null/undefined

            const levelCell = row.insertCell();
            levelCell.classList.add('score-level');
            levelCell.textContent = score.level;

            const movesCell = row.insertCell();
            movesCell.classList.add('score-moves');
            movesCell.textContent = score.moves;

            const timeCell = row.insertCell();
            timeCell.classList.add('score-time');
            timeCell.textContent = `${score.time}s`;

            const dateCell = row.insertCell();
            dateCell.classList.add('score-date');
            dateCell.textContent = score.date || new Date(score.timestamp || Date.now()).toLocaleDateString('es-ES'); // Si 'date' no existe, usa 'timestamp' o fecha actual
        });
    }

    /**
     * Borra todas las puntuaciones de localStorage y actualiza la vista.
     */
    function clearHighscores() {
        if (confirm("¿Estás seguro de que quieres borrar todas las puntuaciones? Esta acción no se puede deshacer.")) {
            try {
                localStorage.removeItem('algorithmExplorerHighscores');
                console.log("Todas las puntuaciones han sido borradas.");
                renderHighscores([]); // Volver a renderizar (mostrará el mensaje de "sin puntuaciones")
            } catch (error) {
                console.error("Error al borrar las puntuaciones:", error);
                alert("Hubo un error al intentar borrar las puntuaciones.");
            }
        }
    }

    // --- Inicialización ---
    const highscores = loadHighscores();
    renderHighscores(highscores);

    if (clearScoresBtn) {
        clearScoresBtn.addEventListener('click', clearHighscores);
    } else {
        console.warn("Botón 'clearScoresBtn' no encontrado en el DOM.");
    }
});