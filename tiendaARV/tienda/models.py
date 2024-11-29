from django.contrib.auth.hashers import make_password
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
import uuid

# Create your models here.
class Marca(models.Model):
    marca_id = models.AutoField(primary_key=True)
    marca_nombre = models.CharField(max_length=30)

    def __str__(self):
        return self.marca_nombre

    class Meta:
        verbose_name_plural = "Marcas"

class Cliente(models.Model):
    cliente_id = models.AutoField(primary_key=True)
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    cliente_vip = models.BooleanField(default=False)
    cliente_saldo = models.IntegerField()
    nombre = models.CharField(max_length=50, blank=True, null=True)
    apellidos = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=50, blank=False, null=False)  # Obligatorio

    def __str__(self):
        return f'{self.usuario.username}'

    def has_email(self):
        return bool(self.email)

    class Meta:
        verbose_name_plural = "Clientes"


class Producto(models.Model):
    producto_nombre = models.CharField(max_length=30)
    producto_modelo = models.CharField(max_length=30)
    producto_unidades = models.PositiveIntegerField()
    producto_precio = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(limit_value=0)])
    producto_descripcion = models.TextField()
    producto_vip = models.BooleanField(default=False)
    marca = models.ForeignKey(Marca, on_delete=models.PROTECT)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    producto_imagen = models.ImageField(upload_to='productos/', blank=True, null=True)

    def __str__(self):
        return f'{self.marca} {self.producto_modelo}'

    @property
    def precio_con_descuento(self):
        if self.descuento:
            return self.producto_precio * (1 - self.descuento / 100)
        return self.producto_precio


class Direccion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    calle = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    pais = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=[('envio', 'Envío'), ('facturacion', 'Facturación')])

    def __str__(self):
        return f"Dirección de {self.tipo} de {self.cliente.usuario.username}"

    class Meta:
        verbose_name_plural = "Direcciones"


class TarjetaPago(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100, choices=[('Visa', 'Visa'), ('Mastercard', 'Mastercard')])
    titular = models.CharField(max_length=100)
    caducidad = models.DateField()

    def __str__(self):
        return f"{self.tipo} - {self.titular}"

    class Meta:
        verbose_name_plural = "Tarjetas de Pago"

class Compra(models.Model):
    compra_fecha = models.DateTimeField(default=timezone.now)
    compra_importe = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(limit_value=0)])
    compra_iva =  models.DecimalField(max_digits=12, decimal_places=2, default=0.21)
    usuario = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    direccion = models.ForeignKey(Direccion, on_delete=models.SET_NULL, blank=False, null=True,related_name='direccion')
    metodo_pago = models.ForeignKey(TarjetaPago, on_delete=models.SET_NULL, blank=False, null=True)
    popularidad = models.IntegerField(default=0)
    metodo_pago = models.CharField(max_length=20, choices=[('stripe', 'Stripe'), ('paypal', 'PayPal')], default='stripe')
    transaccion_id = models.CharField(max_length=255, blank=True, null=True)  # Para almacenar el ID de la transacción

    def __str__(self):
        return f'{self.usuario} {self.compra_fecha}'

    class Meta:
        verbose_name_plural = "Compras"

class producto_compra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    unidades = models.IntegerField()
    precio = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f"{self.producto} {self.compra} {self.unidades} {self.precio}"

    class Meta:
        verbose_name_plural = "Productos compra"


class Comentario(models.Model):
    producto_compra = models.OneToOneField(producto_compra, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField()
    valoracion = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(5)])
    fecha = models.DateTimeField(default=timezone.now)
    moderado_por = models.ManyToManyField(User, related_name='comentarios_moderados', blank=True)
    aprobado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} - {self.itemCompra}'

    class Meta:
        verbose_name_plural = "Comentarios"


class Moderador(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = "Moderadores"

class Wishlist(models.Model):
    cliente = models.ForeignKey('Cliente', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    agregado_fecha = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Wishlist de {self.cliente} - {self.producto}'

    class Meta:
        verbose_name_plural = "Wishlist"
        unique_together = ('cliente', 'producto')

# class Notificacion(models.Model):
#     usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notificaciones")
#     mensaje = models.TextField()
#     fecha_creacion = models.DateTimeField(auto_now_add=True)
#     leido = models.BooleanField(default=False)

#     def __str__(self):
#         return f"Notificación para {self.usuario.username}"