document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('analysis-form');
    const analyzeButton = document.getElementById('analyze-button');
    const overlay = document.getElementById('loadingOverlay');
    const historyButton = document.getElementById('history-button');
    const historyModal = document.getElementById('historyModal');
    const closeModal = document.getElementById('closeModal');
    const historyList = document.getElementById('historyList');

    if (!form || !analyzeButton || !overlay || !historyButton || !historyModal || !closeModal || !historyList) {
        console.error('Missing elements:', { form, analyzeButton, overlay, historyButton, historyModal, closeModal, historyList });
        return;
    }

    // Funcionalidad del botón Analizar
    analyzeButton.addEventListener('click', function(e) {
        e.preventDefault();

        overlay.style.display = 'flex';
        overlay.style.opacity = '1';
        console.log('Overlay shown at:', new Date().toISOString());

        setTimeout(() => {
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                console.warn('Formulario inválido detectado at:', new Date().toISOString());
                setTimeout(() => {
                    overlay.style.display = 'none';
                    console.log('Overlay hidden due to invalid form at:', new Date().toISOString());
                }, 1500);
                return;
            }

            console.log('Form is valid, submitting at:', new Date().toISOString());
            setTimeout(() => {
                form.submit();
            }, 1500);
        }, 100);
    });

    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            overlay.style.display = 'none';
            form.classList.add('was-validated');
            console.warn('Validation failed on submit at:', new Date().toISOString());
        }
    });

    // Funcionalidad del botón Historial
    historyButton.addEventListener('click', function() {
        fetch('/api/historial/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                if (response.status === 403) {
                    historyList.innerHTML = '<li class="list-group-item text-danger">El historial solo está disponible para usuarios Pro.</li>';
                    historyModal.style.display = 'block';
                    console.log('Access denied to history at:', new Date().toISOString());
                } else {
                    throw new Error('Error fetching history');
                }
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                historyList.innerHTML = ''; // Limpiar lista
                data.forEach(item => {
                    const li = document.createElement('li');
                    li.className = 'list-group-item';
                    li.style.cursor = 'pointer';
                    li.textContent = `${item.url} - Puntuación: ${item.puntuacion} - Fecha: ${new Date(item.data).toLocaleDateString()}`;
                    li.addEventListener('click', function() {
                        window.location.href = `/dashboard/${item.id}/`;
                    });
                    historyList.appendChild(li);
                });
                historyModal.style.display = 'block';
                console.log('History loaded at:', new Date().toISOString());
            }
        })
        .catch(error => {
            console.error('Error loading history:', error);
        });
    });

    closeModal.addEventListener('click', function() {
        historyModal.style.display = 'none';
        console.log('History modal closed at:', new Date().toISOString());
    });

    // Función para obtener el token CSRF
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
});