from django.dispatch import receiver
from paypal.standard.ipn.signals import valid_ipn_received
from paypal.standard.models import ST_PP_COMPLETED
from django.core.cache import cache
from django.utils import timezone
from tienda.models import Compra, Cliente, Direccion, Producto, producto_compra

@receiver(valid_ipn_received)
def compra_pagada(sender, **kwargs):
    ipn_obj = sender

    if ipn_obj.payment_status == ST_PP_COMPLETED:
        invoice_id = ipn_obj.invoice
        datos_cache = cache.get(f"paypal_cart_{invoice_id}")

        if not datos_cache:
            return

        try:
            cliente = Cliente.objects.get(pk=datos_cache['usuario_id'])
            direccion = Direccion.objects.get(pk=datos_cache['direccion_id'])
        except (Cliente.DoesNotExist, Direccion.DoesNotExist):
            return

        compra = Compra.objects.create(
            usuario=cliente,
            direccion=direccion,
            metodo_pago="paypal",
            compra_importe=ipn_obj.mc_gross,
            transaccion_id=ipn_obj.txn_id,
            compra_fecha=timezone.now()
        )

        for item in datos_cache['productos']:
            try:
                producto = Producto.objects.get(pk=item['producto_id'])
                producto.reducir_stock(item['unidades'])

                producto_compra.objects.create(
                    compra=compra,
                    producto=producto,
                    unidades=item['unidades'],
                    precio=item['precio']
                )
            except Producto.DoesNotExist:
                continue

        cache.delete(f"paypal_cart_{invoice_id}")