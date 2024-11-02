from django.urls import path
from . import views
from .views import *


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
    path('informe/marcas/', informe_marca.as_view(), name='informe_marca'),
    path('informe/historialcompras/', informe_compra.as_view(), name='informe_compras'),
    path('login/', views.iniciar_sesion.as_view(), name='login'),
    path('logout/', cerrar_sesion.as_view(), name='logout'),
    path('singin/', registrarse.as_view(), name='singin'),
    path('perfil/', perfil.as_view(), name='perfil'),
    path('perfil/editar/<int:pk>/', perfil_update.as_view(), name='editar_perfil'),
    path('informe/historialcompras/crear-comentario/<int:item_compra_id>/', comentario_new.as_view(), name='agregarComentario'),
    path('informe/historialcompras/editar-comentario/<int:item_id>/', comentario_edit.as_view(), name='editarComentario'),
    path('informe/historialcompras/eliminar-comentario/<int:pk>/', comentario_delete.as_view(), name='eliminarComentario'),
    path('moderar-comentarios/', comentario_mod.as_view(), name='moderarComentarios'),
    path('perfil/editar/direccion/<int:pk>/', direccion_edit.as_view(), name='editarDireccion'),
    path('perfil/añadir/direccion/', direccion_new.as_view(), name='añadirDireccion'),
    path('perfil/eliminar/direccion/<int:pk>/', direccion_delete.as_view(),name='confirmarEliminarDireccion'),
    path('perfil/editar/tarjeta-pago/<int:pk>/', tarjeta_edit.as_view(), name='editarTarjetaPago'),
    path('perfil/añadir/tarjeta-pago/', tarjeta_new.as_view(), name='añadirTarjetaPago'),
    path('perfil/eliminar/tarjeta-pago/<int:pk>/', tarjeta_delete.as_view(), name='eliminarTarjetaPago'),
    path('carrito/', carrito.as_view(), name='verCarrito'),
    path('actualizarcarrito/', carrito_update.as_view(), name='actualizarProductoCarrito'),
    path('eliminar-carrito/', carrito_delete.as_view(), name='eliminarProductoCarrito'),
    path('finalizarcompra/', terminar_compra.as_view(), name='finalizarCompra'),
    path('resumencompra/', checkout.as_view(), name='resumenCompra'),

]
