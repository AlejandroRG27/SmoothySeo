document.addEventListener('DOMContentLoaded', function () {
    const cookieModal = new bootstrap.Modal(document.getElementById('cookieModal'));
    const acceptAll = document.querySelector('.accept-all');
    const rejectAll = document.querySelector('.reject-all');
    const manageCookies = document.querySelector('.manage-cookies');

    // Comprobar si ya hay consentimiento
    if (!getCookie('cookie_consent')) {
        cookieModal.show();
    }

    // Aceptar todas las cookies
    acceptAll.addEventListener('click', function () {
        setCookie('cookie_consent', 'all', 365);
        loadAnalyticsCookies();
        cookieModal.hide();
    });

    // Rechazar cookies no esenciales
    rejectAll.addEventListener('click', function () {
        setCookie('cookie_consent', 'essential', 365);
        cookieModal.hide();
    });

    // Mostrar panel de gestión (simulado)
    manageCookies.addEventListener('click', function () {
        alert('Panel de gestión de cookies en desarrollo. Por ahora, selecciona aceptar o rechazar.');
        // Aquí podrías abrir un modal secundario con opciones detalladas
    });

    // Funciones para manejar cookies
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/`;
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Simular carga de cookies analíticas
    function loadAnalyticsCookies() {
        if (getCookie('cookie_consent') === 'all') {
            console.log('Cargando cookies analíticas de Woorank y DeepSeek');
            // Integra aquí las APIs de Woorank y DeepSeek si las tienes
        }
    }
});