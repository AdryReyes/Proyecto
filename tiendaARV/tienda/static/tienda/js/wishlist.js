document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.wishlist-container').forEach(container => {
        container.addEventListener('click', function () {
            const productId = this.getAttribute('data-producto-id');
            const filledIcon = this.querySelector('img[alt="Eliminar de la lista de deseos"]');
            const emptyIcon = this.querySelector('img[alt="Añadir a la lista de deseos"]');
            
            
            const isInWishlist = filledIcon.style.display !== 'none';
            const url = isInWishlist 
                        ? '{% url "remove_from_wishlist" 0 %}'.replace('/0/', `/${productId}/`) 
                        : '{% url "add_to_wishlist" 0 %}'.replace('/0/', `/${productId}/`);

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': '{{ csrf_token }}', 
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al procesar la solicitud.');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'added') {
                    filledIcon.style.display = 'block';
                    emptyIcon.style.display = 'none';
                } else if (data.status === 'removed') {
                    filledIcon.style.display = 'none';
                    emptyIcon.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Ocurrió un error al procesar la solicitud.');
            });
        });
    });
});
