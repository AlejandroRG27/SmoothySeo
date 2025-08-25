// Confirmar que el script se carga
console.log('Script loaded at:', new Date().toISOString());

document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyze-button');
    const overlay = document.getElementById('loadingOverlay');

    if (!analyzeButton || !overlay) {
        console.error('Missing elements:', { analyzeButton, overlay });
        return;
    }

    analyzeButton.addEventListener('click', function(e) {
        e.preventDefault(); // Prevenir envío inmediato
        overlay.style.display = 'flex'; // Mostrar overlay inmediatamente
        console.log('Overlay shown at:', new Date().toISOString());

        // Enviar formulario tras un retraso mínimo
        setTimeout(() => {
            document.getElementById('analysis-form').submit();
        }, 100);
    });
});