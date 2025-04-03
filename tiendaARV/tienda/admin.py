from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Marca)
admin.site.register(Producto)
admin.site.register(Cliente)
admin.site.register(Compra)
admin.site.register(Direccion)
admin.site.register(producto_compra)
admin.site.register(Comentario)
admin.site.register(Moderador)
admin.site.register(Categoria)
admin.site.register(CuentaPago)