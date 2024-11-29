document.addEventListener('DOMContentLoaded', function () {
    const contadorNotificaciones = document.getElementById('contadorNotificaciones');
    const listaNotificaciones = document.getElementById('listaNotificaciones');

    function cargarNotificaciones() {
        fetch('/api/notificaciones/')  // Ruta de la vista de API
            .then(response => response.json())
            .then(notificaciones => {
                listaNotificaciones.innerHTML = '';
                if (notificaciones.length > 0) {
                    contadorNotificaciones.textContent = notificaciones.length;
                    contadorNotificaciones.style.display = 'inline';

                    notificaciones.forEach(notificacion => {
                        const li = document.createElement('li');
                        li.classList.add('dropdown-item');
                        li.textContent = notificacion.mensaje;
                        listaNotificaciones.appendChild(li);
                    });
                } else {
                    contadorNotificaciones.style.display = 'none';
                }
            })
            .catch(error => console.error('Error al obtener notificaciones:', error));
    }

    cargarNotificaciones();
    setInterval(cargarNotificaciones, 60000); // Actualizar cada 60 segundos
});

document.getElementById('campanaNotificaciones').addEventListener('click', () => {
    fetch('/api/notificaciones/leidas/', { method: 'POST', headers: { 'X-CSRFToken': csrftoken } })
        .then(response => response.json())
        .then(data => {
            if (data.estado === 'exito') {
                document.getElementById('contadorNotificaciones').style.display = 'none';
            }
        });
});
