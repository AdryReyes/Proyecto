from django.urls import include, path
from . import views
from .views import *
from django.conf.urls.static import static
from django.conf import settings
from paypal.standard.ipn import urls as paypal_urls


urlpatterns = [
    # path('', views.welcome, name='welcome'),
    path('', welcome.as_view(), name='welcome'),
    path('admin/productos/', producto_admin.as_view(), name='producto_admin'),
    path('productos/<int:pk>/', producto_lista.as_view(), name='producto_lista'),
    path('admin/productos/edit/<int:pk>', producto_edit.as_view(), name='producto_edit'),
    path('admin/productos/delete/<int:pk>', producto_delete.as_view(), name='producto_delete'),
    path('admin/productos/new/', producto_new.as_view(), name='producto_new'),
    path('compra/<int:pk>/', productoCompraDetailView.as_view(), name='compra'),
    path('checkout/<int:pk>/', checkout.as_view(), name='confimar_compra'),
    # path('informe/marcas/', informe_marca.as_view(), name='informe_marca'),
    path('informe/historialcompras/', informe_compra.as_view(), name='informe_compras'),
    path('login/', views.iniciar_sesion.as_view(), name='login'),
    path('logout/', cerrar_sesion.as_view(), name='logout'),
    path('singin/', registrarse.as_view(), name='singin'),
    path('perfil/', perfil.as_view(), name='perfil'),
    path('perfil/editar/<int:pk>/', perfil_update.as_view(), name='editar_perfil'),
    path('informe/historialcompras/crear-comentario/<int:pk>/', comentario_new.as_view(), name='agregarComentario'),
    path('informe/historialcompras/editar-comentario/<int:pk>/', comentario_edit.as_view(), name='editarComentario'),
    path('eliminar-comentario/<int:pk>/', comentario_delete.as_view(), name='eliminarComentario'),
    path('moderar-comentarios/', comentario_mod.as_view(), name='moderarComentarios'),
    path('perfil/editar/direccion/<int:pk>/', direccion_edit.as_view(), name='editarDireccion'),
    path('perfil/añadir/direccion/', direccion_new.as_view(), name='añadirDireccion'),
    path('perfil/eliminar/direccion/<int:pk>/', direccion_delete.as_view(),name='confirmarEliminarDireccion'),
    path('carrito/', carrito.as_view(), name='verCarrito'),
    path('actualizarcarrito/', views.carrito_update, name='actualizarProductoCarrito'),
    path('eliminar-carrito/', carrito_delete.as_view(), name='eliminarProductoCarrito'),
    path('finalizarcompra/<int:producto_id>/', views.finalizar_compra, name='finalizarCompra'),
    path('resumencompra/', checkout.as_view(), name='resumenCompra'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/toggle/<int:producto_id>/', ToggleWishlistView.as_view(), name='toggle_wishlist'),
    path('productos/buscar/', BuscarPorNombreView.as_view(), name='buscar_por_nombre'),
    path('productos/<str:categoria_nombre>/', ProductosPorCategoriaView.as_view(), name='productos_por_categoria'),
    path('recuperar-contraseña/', RecuperarContrasenaView.as_view(), name='recuperar_contraseña'),
    path('captcha/', include('captcha.urls')),
    # path('gestionar-cuentas/', views.gestionar_cuentas, name='gestionar_cuentas'),
    path('compra-exitosa/', views.compra_exitosa, name='compra_exitosa'),
    path('finalizar-compra/', views.finalizar_compra_carrito, name='finalizar_compra'),
    path('responder-comentarios/<int:pk>', ResponderComentarioView.as_view(), name='responderComentario'),
    # path('productos/buscar/<str:categoria_nombre>/', views.BuscarPorNombreView.as_view(), name='filtro_busqueda_categoria'),
    # path('productos/<str:categoria_nombre>/filtro/', ProductoFiltroPorMarca.as_view(), name='filtro_marca'),
    # path('productos/<str:categoria_nombre>/precio/', ProductoFiltroPorPrecio.as_view(), name='filtro_precio'),
    path('categoria/<str:categoria_nombre>/', ProductoFiltroView.as_view(), name='filtro_categoria'),
    path('paypal/', include(paypal_urls)),
    path('historial/exportar-pdf/', views.exportar_historial_pdf, name='exportar_historial_pdf'),
    path('paypal/exito/', views.pago_exitoso, name='paypal_exito'),
    path('admin/marca/nueva/', marca_new.as_view(), name='marca_new'),
    path('admin/categoria/nueva/', categoria_new.as_view(), name='categoria_new'),
    # path('paypal/cancelado/', views.paypal_cancelado, name='paypal_cancelado'),
    path('admin/ranking-marcas/', MarcaRankingView.as_view(), name='ranking_marcas'),
    path('admin/ranking-productos/', ProductoRankingView.as_view(), name='ranking_productos'),
    path('admin/ranking-clientes/', ClienteRankingView.as_view(), name='ranking_clientes'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)