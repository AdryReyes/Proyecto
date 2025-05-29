from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Sum, Avg, F, ExpressionWrapper, DecimalField, Q, ExpressionWrapper
from django.dispatch import receiver
from django.forms import FloatField
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from decimal import Decimal, InvalidOperation
from django.core.cache import cache
from paypal.standard.models import ST_PP_COMPLETED
from paypal.standard.forms import PayPalPaymentsForm
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator

import paypalrestsdk
from paypalrestsdk import Payment
from requests import request


from .models import *
from .forms import *

from django.utils import timezone
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseRedirect




from django.db.models import Count

# paypalrestsdk.configure({
#     "mode": "sandbox", 
#     "client_id": settings.PAYPAL_CLIENT_ID,
#     "client_secret": settings.PAYPAL_CLIENT_SECRET,
# })


class welcome(ListView, FormView):
    template_name = 'tienda/index.html'
    form_class = FilterForm
    context_object_name = 'productos'

    def get_queryset(self):
        queryset = Producto.objects.all()

        # Ordenar según el parámetro de la solicitud
        orden = self.request.GET.get('orden', 'recientes')
        if orden == 'mas_vendidos':
            queryset = queryset.annotate(num_ventas=Count('producto_compra')).order_by('-num_ventas')
        elif orden == 'recientes':
            queryset = queryset.order_by('-fecha_creacion')

        # Aplicar filtros del formulario
        if self.request.method == 'POST':
            form = self.get_form()
            if form.is_valid():
                producto_nombre = form.cleaned_data['nombre']
                marca = form.cleaned_data['marca']
                if producto_nombre:
                    queryset = queryset.filter(producto_nombre__icontains=producto_nombre)
                if marca:
                    queryset = queryset.filter(marca__in=marca)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Agregar categorías al contexto
        context['categorias'] = Categoria.objects.all()

        # Añadir datos adicionales al contexto
        context['form'] = self.get_form()
        context['marcas'] = Marca.objects.all()
        context['productos_mas_vendidos'] = Producto.objects.annotate(num_ventas=Count('producto_compra')).order_by('-num_ventas')[:5]
        context['productos_recientes'] = Producto.objects.order_by('-fecha_creacion')[:5]
        context['productos_recomendados'] = Producto.objects.order_by('?')[:5]

        return context

    def form_valid(self, form):
        # Renderizar con el queryset filtrado
        return self.render_to_response(self.get_context_data())

    def form_invalid(self, form):
        # Renderizar con los errores del formulario
        return self.render_to_response(self.get_context_data(form=form))


    

class producto_lista(DetailView):
    model = Producto
    template_name = 'tienda/producto_detalle.html'
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = self.get_object()
        context['producto'] = producto

        comentarios = Comentario.objects.filter(producto_compra__producto=producto)
        context['comentarios'] = comentarios

        cliente = None
        cliente_ha_comprado = False
        en_wishlist = False  

        if self.request.user.is_authenticated:
            try:
                cliente = self.request.user.cliente
                producto_compras = producto_compra.objects.filter(compra__usuario=cliente, producto=producto)
                cliente_ha_comprado = producto_compras.exists()

                
                en_wishlist = Wishlist.objects.filter(cliente=cliente, producto=producto).exists()

            except Cliente.DoesNotExist:
                pass

        ya_comento = comentarios.filter(user=self.request.user).exists() if self.request.user.is_authenticated else False

        # Añadir todo al contexto
        context['categorias'] = Categoria.objects.all()
        context['cliente_ha_comprado'] = cliente_ha_comprado
        context['cliente'] = cliente
        context['ya_comento'] = ya_comento
        context['en_wishlist'] = en_wishlist

        return context
    

@method_decorator(staff_member_required, name='dispatch')
class producto_admin(ListView):
	model = Producto
	template_name = 'tienda/admin.html'
	context_object_name = 'productos'


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class producto_edit(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'tienda/producto_edit.html'

    def form_valid(self, form):
        # Procesamos la imagen cargada
        producto = form.save(commit=False)
        producto.author = self.request.user  # Si este campo está en tu modelo
        producto.published_date = timezone.now()

        # Guardamos el producto
        producto.save()

        # Guardamos la relación del archivo
        form.save_m2m()

        return redirect('producto_admin')



@method_decorator(staff_member_required, name='dispatch')
@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class producto_delete(DeleteView):
		model = Producto
		success_url = reverse_lazy('producto_admin')
		template_name = 'tienda/producto_edit.html'


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class producto_new(CreateView):
    model = Producto
    template_name = 'tienda/producto_new.html'
    form_class = ProductoForm
    success_url = reverse_lazy('producto_admin')

    def form_valid(self, form):
        # Asegurarnos de que el archivo de imagen se procesa
        producto = form.save(commit=False)
        producto.author = self.request.user  # Si este campo está en tu modelo
        producto.published_date = timezone.now()

        # Guardamos el producto
        producto.save()

        # Guardamos la relación del archivo
        form.save_m2m()

        return redirect('producto_admin')



# @method_decorator(staff_member_required, name='dispatch')
# @method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
# class producto_info(DetailView):
# 	model = Producto
# 	template_name = 'tienda/producto_info.html'
# 	context_object_name = 'producto'


@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
@method_decorator(transaction.atomic, name='dispatch')
class productoCompraDetailView(DetailView):
    model = Producto
    template_name = 'tienda/compra.html'
    context_object_name = 'producto'

    def post(self, request, *args, **kwargs):
        producto = self.get_object()
        form = AgregarProductoForm(request.POST)
        if form.is_valid():
            cantidad = form.cleaned_data['cantidad']

            carrito = request.session.get('carrito', {})
            producto_id = str(producto.pk)
            if producto_id in carrito:
                carrito[producto_id]['cantidad'] += cantidad
            else:
                carrito[producto_id] = {
                    'nombre': producto.producto_nombre,
                    'precio': float(producto.producto_precio),
                    'cantidad': cantidad,
                }
            request.session['carrito'] = carrito
            return redirect(request.META.get('HTTP_REFERER', 'producto_lista'))
        else:
            return render(request, self.template_name, {'producto': producto, 'form': form})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = self.get_object()

        items_compra = producto_compra.objects.filter(producto=producto)  # Aquí usamos el modelo correcto
        compras = [item.compra for item in items_compra]

        comentarios = Comentario.objects.filter(producto_compra__in=items_compra, aprobado=True)

        valoracion_media = comentarios.aggregate(avg_valoracion=Avg('valoracion'))['avg_valoracion']

        context['comentarios'] = comentarios
        context['valoracion_media'] = round(valoracion_media, 1) if valoracion_media else None

        return context

class iniciar_sesion(LoginView):
	template_name = 'tienda/login.html'
	form_class = LoginForm
	success_url = '/tienda'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['accion'] = 'Iniciar Sesión'
		return context

	def form_valid(self, form):
		username = form.cleaned_data.get("username")
		password = form.cleaned_data.get("password")
		next_ruta = self.request.GET.get('next', self.success_url)

		user = authenticate(request=self.request, username=username, password=password)

		if user is not None:
			login(self.request, user)
			return redirect(next_ruta)
		else:
			messages.error(self.request, 'Las credenciales no son válidas')

		return super().form_invalid(form)



class cerrar_sesion(LogoutView):
	next_page = 'welcome'


class registrarse(CreateView):
    template_name = 'tienda/login.html'  
    form_class = SignInForm
    success_url = reverse_lazy('welcome')  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accion'] = 'Crear Cuenta'  
        return context

    def form_valid(self, form):
        response = super().form_valid(form)  
        user = self.object  

        cliente = Cliente(
            usuario=user, 
            cliente_vip=False,  
            email=form.cleaned_data['email'],  
            nombre=form.cleaned_data['nombre'],  
            apellidos=form.cleaned_data['apellidos']  
        )
        cliente.save()  
        login(self.request, user)  
        return response

@method_decorator(staff_member_required, name='dispatch')
@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class informe_marca(TemplateView):
    template_name = 'tienda/marcas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        marcas = Marca.objects.all()
        productos = Producto.objects.all()

        context['marcas'] = marcas
        context['productos'] = productos

        return context


@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class informe_compra(TemplateView):
    template_name = 'tienda/detalle_compra.html'

    def dispatch(self, request, *args, **kwargs):
        # Eliminar compra si se ha enviado por POST
        if 'eliminar_compra_id' in request.POST:
            compra_id = request.POST['eliminar_compra_id']
            try:
                compra = Compra.objects.get(pk=compra_id)
                compra.delete()
                messages.success(request, 'La compra ha sido eliminada correctamente.')
            except Compra.DoesNotExist:
                messages.error(request, 'La compra que intenta eliminar no existe.')
            return redirect(request.path)  # Redirigir a la misma URL
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = get_object_or_404(Cliente, usuario=self.request.user)

        # Obtener fechas del formulario GET
        fecha_inicio = self.request.GET.get('fecha_inicio')
        fecha_fin = self.request.GET.get('fecha_fin')

        # Filtrar compras por usuario y fechas
        compras = Compra.objects.filter(usuario=cliente).order_by('-compra_fecha')
        if fecha_inicio:
            compras = compras.filter(compra_fecha__date__gte=parse_date(fecha_inicio))
        if fecha_fin:
            compras = compras.filter(compra_fecha__date__lte=parse_date(fecha_fin))

        # Paginación
        paginator = Paginator(compras, 5) 
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        # Añadir comentarios y valoraciones a cada producto por compra
        compras_con_comentarios = []
        for compra in page_obj:
            productos_compra = producto_compra.objects.filter(compra=compra)
            comentarios_por_compra = []

            for producto in productos_compra:
                comentarios = Comentario.objects.filter(
                    user=self.request.user,
                    producto_compra__producto=producto.producto
                )
                promedio_valoracion = comentarios.aggregate(
                    valoracion_promedio=Avg('valoracion')
                )['valoracion_promedio']
                comentarios_por_compra.append((producto, comentarios, promedio_valoracion))

            compras_con_comentarios.append((compra, comentarios_por_compra))

        # Contexto final
        context['compras_con_comentarios'] = compras_con_comentarios
        context['page_obj'] = page_obj
        context['fecha_inicio'] = fecha_inicio
        context['fecha_fin'] = fecha_fin
        context['categorias'] = Categoria.objects.all()
        return context

@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class perfil(TemplateView):
    template_name = 'tienda/perfil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cliente = Cliente.objects.get(usuario=user)
        direcciones_envio = Direccion.objects.filter(cliente=cliente)
        direcciones_facturacion = Direccion.objects.filter(cliente=cliente)
        # tarjetas_pago = TarjetaPago.objects.filter(cliente=cliente)
        context['cliente'] = cliente
        context['direcciones_envio'] = direcciones_envio
        context['direcciones_facturacion'] = direcciones_facturacion
        # context['tarjetas_pago'] = tarjetas_pago
        return context

@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class perfil_update(UpdateView):
    model = Cliente
    form_class = EditarDatosForm
    template_name = 'tienda/modificar_perfil.html'
    success_url = reverse_lazy('perfil')

    def form_valid(self, form):
        user = self.request.user
        cliente = user.cliente

        # Actualización del usuario y cliente
        user.email = form.cleaned_data['email']
        user.first_name = form.cleaned_data['nombre']
        user.last_name = form.cleaned_data['apellidos']
        cliente.nombre = form.cleaned_data['nombre']
        cliente.apellidos = form.cleaned_data['apellidos']
        cliente.email = form.cleaned_data['email']

        # Actualización del nombre de usuario
        nuevo_usuario = form.cleaned_data.get('nuevo_usuario')
        if nuevo_usuario:
            user.username = nuevo_usuario

        user.save()
        cliente.save()

        return redirect(self.success_url)



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class direccion_new(CreateView):
    model = Direccion
    form_class = DireccionForm
    template_name = 'tienda/editar_direccion.html'
    success_url = reverse_lazy('perfil')

    def form_valid(self, form):
        cliente = self.request.user.cliente
        form.instance.cliente = cliente
        return super().form_valid(form)



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class direccion_edit(UpdateView):
    model = Direccion
    form_class = DireccionForm
    template_name = 'tienda/editar_direccion.html'
    success_url = reverse_lazy('perfil')

    def get_object(self, queryset=None):
        try:
            direccion = Direccion.objects.get(cliente__user=self.request.user, pk=self.kwargs['pk'])
        except Direccion.DoesNotExist:
            direccion = None
        return direccion

    def form_valid(self, form):
        cliente = self.request.user.cliente
        form.instance.cliente = cliente
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object:
            return redirect('añadirDireccion')
        return super().dispatch(request, *args, **kwargs)



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class direccion_delete(DetailView):
    model = Direccion
    template_name = 'tienda/borrar_direccion.html'

    def post(self, request, *args, **kwargs):
        direccion = get_object_or_404(Direccion, pk=self.kwargs['pk'])
        direccion.delete()
        return redirect('perfil')




@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class carrito(TemplateView):
    template_name = 'tienda/ver_carrito.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrito = self.request.session.get('carrito', {})
        productos_carrito = []
        total_precio = Decimal('0.00')

        for producto_id, info_producto in carrito.items():
            producto = Producto.objects.get(id=producto_id)
            cantidad = info_producto['cantidad']
            subtotal = producto.precio_con_descuento * cantidad
            total_precio += subtotal

            productos_carrito.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })

        #  Generar invoice único
        invoice = str(uuid.uuid4())

        #  Guardar en caché la compra
        cliente = self.request.user.cliente
        direcciones = cliente.direccion_set.all()
        direccion = direcciones.first() if direcciones.exists() else None

        cache.set(f"paypal_cart_{invoice}", {
            'usuario_id': cliente.cliente_id,
            'direccion_id': direccion.id if direccion else None,
            'importe': float(total_precio),
            'productos': [
                {
                    'producto_id': p['producto'].id,
                    'unidades': p['cantidad'],
                    'precio': float(p['producto'].producto_precio)
                } for p in productos_carrito
            ]
        }, timeout=3600)

        # ✅ Enviar variables al template
        context['productos_carrito'] = productos_carrito
        context['total_precio'] = total_precio
        context['invoice'] = invoice

        return context


@login_required(login_url='/tienda/login/')
def carrito_update(request):
    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('verCarrito')

    # Si se pulsó el botón de eliminar, se procesa directamente
    if 'eliminar' in request.POST:
        producto_id = request.POST['eliminar']
        if producto_id in carrito:
            producto = get_object_or_404(Producto, id=producto_id)
            del carrito[producto_id]
            messages.success(request, f"Se eliminó '{producto.producto_nombre}' del carrito.")
            request.session['carrito'] = carrito
        else:
            messages.error(request, "El producto no estaba en el carrito.")
        return redirect('verCarrito')

    # Si no se pulsó "eliminar", se actualizan cantidades
    ajustes_realizados = False

    for key in request.POST:
        if key.startswith("cantidad_"):
            producto_id = key.split("_")[1]
            try:
                cantidad = int(request.POST[key])
            except ValueError:
                continue  # ignorar valores inválidos

            if producto_id in carrito:
                producto = get_object_or_404(Producto, id=producto_id)

                if cantidad <= 0:
                    del carrito[producto_id]
                    messages.info(request, f"'{producto.producto_nombre}' fue eliminado del carrito (cantidad 0).")
                    ajustes_realizados = True
                elif cantidad > producto.producto_unidades:
                    carrito[producto_id]['cantidad'] = producto.producto_unidades
                    messages.warning(request, f"La cantidad de '{producto.producto_nombre}' fue ajustada al máximo disponible ({producto.producto_unidades}).")
                    ajustes_realizados = True
                else:
                    carrito[producto_id]['cantidad'] = cantidad

    request.session['carrito'] = carrito

    if ajustes_realizados:
        messages.info(request, "Se ajustaron algunas cantidades en el carrito.")

    messages.success(request, "El carrito se actualizó correctamente.")
    return redirect('verCarrito')



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class carrito_delete(DeleteView):
    def post(self, request, *args, **kwargs):
        producto_id = request.POST.get('producto_id')

        carrito = request.session.get('carrito', {})
        if producto_id in carrito:
            del carrito[producto_id]
            request.session['carrito'] = carrito
            messages.success(request, "El producto se eliminó del carrito correctamente.")
        else:
            messages.error(request, "El producto no está en el carrito.")

        return redirect('verCarrito')

    def get_success_url(self):
        return reverse_lazy('verCarrito')



@login_required(login_url='/tienda/login/')

def finalizar_compra(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    cliente = request.user.cliente
    cuentas = cliente.cuentas.all()
    direcciones = cliente.direccion_set.all()

    if not direcciones.exists():
        return render(request, 'tienda/error.html', {"mensaje": "No tienes direcciones configuradas."})

    # Precio final con descuento si aplica
    precio_final = producto.precio_con_descuento

    # Generar un invoice único
    invoice = str(uuid.uuid4())

    # Guardar información en caché para recuperarla después en pago_exitoso
    cache.set(f"paypal_cart_{invoice}", {
        'usuario_id': cliente.cliente_id,
        'direccion_id': direcciones.first().id,
        'importe': float(precio_final),
        'productos': [{
            'producto_id': producto.id,
            'unidades': 1,
            'precio': float(precio_final)
        }]
    }, timeout=3600)

    # Si se desea también permitir pago interno con tarjeta
    if request.method == 'POST':
        form = SeleccionarCuentaForm(request.POST, cliente=cliente)
        if form.is_valid():
            try:
                producto.reducir_stock(1)
                compra = Compra.objects.create(
                    usuario=cliente,
                    direccion=direcciones.first(),
                    metodo_pago=form.cleaned_data['metodo_pago'],
                    compra_importe=precio_final,
                    transaccion_id='',
                    compra_fecha=timezone.now()
                )

                producto_compra.objects.create(
                    compra=compra,
                    producto=producto,
                    unidades=1,
                    precio=precio_final
                )

                return redirect('compra_exitosa')
            except ValueError as e:
                return render(request, 'tienda/error.html', {'mensaje': str(e)})

    else:
        form = SeleccionarCuentaForm(cliente=cliente)

    return render(request, 'tienda/terminar_compra.html', {
        'producto': producto,
        'form': form,
        'cuentas': cuentas,
        'direcciones': direcciones,
        'invoice': invoice  # Se usa en el formulario PayPal
    })

@login_required(login_url='/tienda/login/')
def gestionar_cuentas(request):
    cliente = request.user.cliente
    if request.method == 'POST':
        form = CrearCuentaForm(request.POST)
        if form.is_valid():
            cuenta = form.save(commit=False)
            cuenta.cliente = cliente
            cuenta.save()
            return redirect('gestionar_cuentas')
    else:
        form = CrearCuentaForm()
    cuentas = cliente.cuentas.all()
    return render(request, 'tienda/gestionar_cuentas.html', {
        'form': form,
        'cuentas': cuentas,
    })

def finalizar_compra_carrito(request):
    cliente = request.user.cliente
    cuentas = cliente.cuentas.all()
    direcciones = cliente.direccion_set.all()

    carrito = request.session.get('carrito', {})
    if not carrito:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('index')

    productos_carrito = []
    total_precio = 0
    stock_insuficiente = False

    for producto_id, info_producto in carrito.items():
        producto = Producto.objects.get(id=producto_id)
        cantidad_producto = info_producto['cantidad']

        if cantidad_producto > producto.producto_unidades:
            stock_insuficiente = True
            mensaje_error = f"No hay suficiente stock para el producto {producto.producto_nombre}. Solo quedan {producto.producto_unidades} unidades."
            messages.error(request, mensaje_error)

        subtotal_producto = producto.producto_precio * cantidad_producto
        productos_carrito.append({
            'producto': producto,
            'cantidad': cantidad_producto,
            'subtotal': subtotal_producto
        })
        total_precio += subtotal_producto

    if stock_insuficiente:
        return redirect('verCarrito')

    if request.method == 'POST':
        form = SeleccionarCuentaForm(request.POST, cliente=cliente)
        if form.is_valid():
            # Crear la compra
            compra = Compra.objects.create(
                usuario=cliente,
                direccion=direcciones.first(),
                metodo_pago=form.cleaned_data['metodo_pago'],
                compra_importe=total_precio,
                transaccion_id='',  # Se llenará después del pago real
                compra_fecha=timezone.now()
            )

            # Registrar productos comprados
            for producto_id, info_producto in carrito.items():
                producto = Producto.objects.get(id=producto_id)
                producto_compra.objects.create(
                    compra=compra,
                    producto=producto,
                    unidades=info_producto['cantidad'],
                    precio=producto.producto_precio
                )

            # Vaciar carrito
            request.session['carrito'] = {}
            messages.success(request, "Compra realizada con éxito.")
            return redirect('compra_exitosa')

        else:
            return render(request, 'tienda/ver_carrito.html', {
                'form': form,
                'cuentas': cuentas,
                'direcciones': direcciones,
                'productos_carrito': productos_carrito,
                'total_precio': total_precio
            })

    else:
        form = SeleccionarCuentaForm(cliente=cliente)

    return render(request, 'tienda/ver_carrito.html', {
        'form': form,
        'cuentas': cuentas,
        'direcciones': direcciones,
        'productos_carrito': productos_carrito,
        'total_precio': total_precio
    })



@login_required(login_url='/tienda/login/')
def compra_exitosa(request):
    return render(request, 'tienda/compra_exitosa.html', {'mensaje': '¡Compra realizada con éxito!'})

@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class checkout(DetailView):
    model = Compra
    template_name = 'tienda/resumen_compra.html'
    context_object_name = 'ultima_compra'

    def get_object(self, queryset=None):
        usuario = self.request.user
        cliente = get_object_or_404(Cliente, usuario=usuario)
        return Compra.objects.filter(usuario=cliente).latest('compra_fecha')


@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class comentario_new(FormView):
    form_class = ComentarioForm
    template_name = 'tienda/comentario_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ProductoCompra_instance = get_object_or_404(producto_compra, pk=self.kwargs['pk'])
        context['producto'] = ProductoCompra_instance.producto
        return context

    def form_valid(self, form):
        ProductoCompra_instance = get_object_or_404(producto_compra, pk=self.kwargs['pk'])

        if ProductoCompra_instance.compra.usuario != self.request.user.cliente:
            return HttpResponseForbidden("No tienes permiso para comentar este producto.")

        Comentario.objects.create(
            producto_compra=ProductoCompra_instance,
            user=self.request.user,
            comentario=form.cleaned_data['comentario'],
            valoracion=form.cleaned_data['valoracion'],
            aprobado=False,
        )

        return redirect('producto_lista', pk=ProductoCompra_instance.producto.id)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class comentario_edit(UpdateView):
    model = Comentario
    fields = ['comentario', 'valoracion']
    template_name = 'tienda/editar_comentario.html'

    def get_success_url(self):
        comentario = self.get_object()
        producto_pk = comentario.producto_compra.producto.pk  # Asegúrate que esto sea correcto
        return reverse_lazy('producto_lista', kwargs={'pk': producto_pk})

    def test_func(self):
        comentario = self.get_object()
        return self.request.user == comentario.user or self.request.user.is_staff

    def form_valid(self, form):
        # Opcional: lógica personalizada
        if self.request.user.is_staff:
            form.instance.moderado_por.add(self.request.user)  # Si es staff, agrega como moderador
        return super().form_valid(form)


class comentario_delete(DeleteView):
    model = Comentario
    template_name = 'tienda/eliminar_comentario.html'

    def get_success_url(self):
        # Obtenemos el producto relacionado al comentario
        comentario = self.get_object()
        producto_pk = comentario.producto_compra.producto.pk  # Ajusta si el modelo tiene otro nombre
        return reverse_lazy('producto_lista', kwargs={'pk': producto_pk})

    def test_func(self):
        comentario = self.get_object()
        return self.request.user == comentario.user or self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        comentario = self.get_object()
        # Eliminar las respuestas antes de eliminar el comentario
        comentario.comentario_set.all().delete()  # Eliminar todas las respuestas asociadas al comentario
        return super().delete(request, *args, **kwargs)  # Luego eliminar el comentario

class ResponderComentarioView(View):
    def get(self, request, pk):
        comentario = get_object_or_404(Comentario, pk=pk)
        form = ResponderComentarioForm()  # Creamos una instancia del formulario vacío
        return render(request, 'tienda/responder_comentario.html', {'form': form, 'comentario': comentario})

    def post(self, request, pk):
        comentario = get_object_or_404(Comentario, pk=pk)
        form = ResponderComentarioForm(request.POST)

        if form.is_valid():
            # Crear una nueva respuesta
            Comentario.objects.create(
                producto_compra=comentario.producto_compra,
                user=request.user,
                comentario=form.cleaned_data['comentario'],
                valoracion=form.cleaned_data['valoracion'],
                respuesta_a=comentario,  # Relacionar la respuesta con el comentario original
                aprobado=True,  # Aprobado por defecto
            )
            return redirect('producto_lista', pk=comentario.producto_compra.producto.pk)  # Redirige al detalle del producto
        return render(request, 'tienda/responder_comentario.html', {'form': form, 'comentario': comentario})

class comentario_mod(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Comentario
    template_name = 'tienda/moderar_comentario.html'
    context_object_name = 'comentarios_pendientes'
    permission_required = [
        'tienda.add_comentario',
        'tienda.change_comentario',
        'tienda.delete_comentario',
        'tienda.view_comentario',
    ]

    def get_queryset(self):
        return Comentario.objects.filter(aprobado=False)

    def post(self, request, *args, **kwargs):
        item_compra_ids = request.POST.getlist('item_compra_ids[]')
        for item_compra_id in item_compra_ids:
            item_compra = get_object_or_404(producto_compra, pk=item_compra_id)
            aprobado = request.POST.get(f'aprobado_{item_compra_id}', False)
            rechazado = request.POST.get(f'rechazado_{item_compra_id}', False)
            if aprobado == 'True':
                comentario = Comentario.objects.get(producto_compra=item_compra)
                comentario.aprobado = True
                comentario.save()
            elif rechazado == 'True':
                comentario = Comentario.objects.get(producto_compra=item_compra)
                comentario.delete()
        return redirect('moderarComentarios')

    

class WishlistView(LoginRequiredMixin, ListView):
    model = Wishlist
    template_name = 'tienda/wishlist.html'
    context_object_name = 'wishlist_items'

    def get_queryset(self):

        cliente = self.request.user.cliente  
        return Wishlist.objects.filter(cliente=cliente)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()  
        return context  


class ToggleWishlistView(LoginRequiredMixin, View):
    def post(self, request, producto_id):
        producto = get_object_or_404(Producto, id=producto_id)

        try:
            cliente = Cliente.objects.get(usuario=request.user)
        except Cliente.DoesNotExist:
            messages.error(request, "Debes ser un cliente para modificar tu lista de deseos.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        wishlist_item = Wishlist.objects.filter(cliente=cliente, producto=producto).first()

        if wishlist_item:
            wishlist_item.delete()
            messages.info(request, f"'{producto.producto_nombre}' se ha eliminado de tu lista de deseos.")
        else:
            Wishlist.objects.create(cliente=cliente, producto=producto)
            messages.success(request, f"'{producto.producto_nombre}' se ha añadido a tu lista de deseos.")

        return redirect(request.META.get('HTTP_REFERER', '/'))


class ProductosPorCategoriaView(ListView):
    template_name = 'tienda/categoria.html'
    context_object_name = 'productos'
    paginate_by = 15  # 🔹 Mostrar 15 productos por página

    def get_queryset(self):
        # Obtener categoría según el slug pasado en la URL
        self.categoria = get_object_or_404(Categoria, nombre=self.kwargs['categoria_nombre'])
        return Producto.objects.filter(categoria=self.categoria)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categoria'] = self.categoria
        context['categorias'] = Categoria.objects.all()
        context['marcas'] = Producto.objects.filter(categoria=self.categoria).values('marca__marca_nombre').distinct()
        context['precio_min'] = self.request.GET.get('precio_min', '')
        context['precio_max'] = self.request.GET.get('precio_max', '')
        context['query_params'] = self.request.GET.copy()  # 🔹 Para conservar filtros en los enlaces de paginación
        return context


class RecuperarContrasenaView(View):
    template_name = 'tienda/recuperar_contraseña.html'

    def get(self, request):
        form = RecuperarContrasenaForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = RecuperarContrasenaForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            nueva_contrasena = form.cleaned_data.get('nueva_contrasena')

            user = User.objects.get(username=username, email=email)

            if nueva_contrasena:
                # Cambiar la contraseña del usuario
                user.password = make_password(nueva_contrasena)
                user.save()
                return redirect('login')  # Redirige al login tras cambiar la contraseña
            else:
                # Si no hay nueva contraseña, muestra un campo para establecerla
                form.fields['nueva_contrasena'].required = True
                return render(request, self.template_name, {
                    'form': form,
                    'password_step': True,
                })

        return render(request, self.template_name, {'form': form})
    
    
class BuscarPorNombreView(ListView):
    model = Producto
    template_name = 'tienda/busqueda.html'
    context_object_name = 'productos'
    paginate_by = 9

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        queryset = Producto.objects.all()

        if query:
            queryset = queryset.filter(producto_nombre__icontains=query)

        marcas_seleccionadas = self.request.GET.getlist('marcas')
        if marcas_seleccionadas:
            queryset = queryset.filter(marca__marca_nombre__in=marcas_seleccionadas)

        rebajados = self.request.GET.get('rebajados')
        if rebajados:
            queryset = queryset.filter(descuento__gt=0)

        # ✅ Anotar correctamente usando la clase, no una instancia
        queryset = queryset.annotate(
            precio_descuento_db=ExpressionWrapper(
                F('producto_precio') - (F('producto_precio') * F('descuento') / 100),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        )

        precio_min = self.request.GET.get('precio_min')
        precio_max = self.request.GET.get('precio_max')

        if precio_min:
            try:
                queryset = queryset.filter(precio_descuento_db__gte=precio_min)
            except ValueError:
                pass

        if precio_max:
            try:
                queryset = queryset.filter(precio_descuento_db__lte=precio_max)
            except ValueError:
                pass

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['marcas'] = Producto.objects.values('marca__marca_nombre').distinct()
        context['q'] = self.request.GET.get('q', '')
        context['marcas_seleccionadas'] = self.request.GET.getlist('marcas')
        context['rebajados'] = 'rebajados' in self.request.GET
        context['precio_min'] = self.request.GET.get('precio_min', '')
        context['precio_max'] = self.request.GET.get('precio_max', '')
        return context

class ProductoFiltroView(View):
    def get(self, request, categoria_nombre):
        categoria = get_object_or_404(Categoria, nombre=categoria_nombre)
        productos = Producto.objects.filter(categoria=categoria)

        # Filtro por marca
        marcas_seleccionadas = request.GET.getlist('marcas')
        if marcas_seleccionadas:
            productos = productos.filter(marca__marca_nombre__in=marcas_seleccionadas)

        # Filtro por rebajados
        rebajados = request.GET.get('rebajados')
        if rebajados:
            productos = productos.filter(descuento__gt=0)

        # Marcas disponibles
        marcas = Producto.objects.filter(categoria=categoria).values('marca__marca_nombre').distinct()

        # Filtro por precio
        precio_min = request.GET.get('precio_min')
        precio_max = request.GET.get('precio_max')
        if precio_min or precio_max:
            precio_min = float(precio_min) if precio_min else 0
            precio_max = float(precio_max) if precio_max else float('inf')
            productos = [p for p in productos if precio_min <= p.precio_final <= precio_max]
        else:
            productos = list(productos)

        # 🔹 Paginación
        paginator = Paginator(productos, 15)  # 15 productos por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'tienda/categoria.html', {
            'categoria': categoria,
            'productos': page_obj.object_list,
            'page_obj': page_obj,
            'marcas': marcas,
            'marcas_seleccionadas': marcas_seleccionadas,
            'precio_min': request.GET.get('precio_min', ''),
            'precio_max': request.GET.get('precio_max', ''),
            'rebajados': rebajados,
            'query_params': request.GET.copy(), 
        })



def pago_exitoso(request):
    invoice_id = request.GET.get('invoice')

    if not invoice_id:
        return redirect('index')

    datos_cache = cache.get(f"paypal_cart_{invoice_id}")
    if not datos_cache:
        return render(request, 'tienda/pago_error.html', {"mensaje": "No se encontró la información del carrito."})

    try:
        cliente = Cliente.objects.get(cliente_id=datos_cache['usuario_id'])
        direccion = Direccion.objects.get(pk=datos_cache['direccion_id'])
    except (Cliente.DoesNotExist, Direccion.DoesNotExist):
        return render(request, 'tienda/pago_error.html', {"mensaje": "Usuario o dirección inválida."})

    compra = Compra.objects.create(
        usuario=cliente,
        direccion=direccion,
        metodo_pago="paypal",
        transaccion_id=invoice_id,
        compra_importe=datos_cache['importe'],
        compra_fecha=timezone.now()
    )

    for item in datos_cache['productos']:
        try:
            producto = Producto.objects.get(pk=item['producto_id'])
            producto.reducir_stock(item['unidades'])  # importante para el stock
            producto_compra.objects.create(
                compra=compra,
                producto=producto,
                unidades=item['unidades'],
                precio=item['precio'],
            )
        except Producto.DoesNotExist:
            continue

    request.session['carrito'] = {}
    cache.delete(f"paypal_cart_{invoice_id}")

    return render(request, 'tienda/pago_exitoso.html', {'compra': compra})

@login_required
def exportar_historial_pdf(request):
    cliente = get_object_or_404(Cliente, usuario=request.user)

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    page_number = request.GET.get('page')

    compras = Compra.objects.filter(usuario=cliente).order_by('-compra_fecha')

    if fecha_inicio and fecha_inicio != "None":
        fecha_inicio_parsed = parse_date(fecha_inicio)
        if fecha_inicio_parsed:
            compras = compras.filter(compra_fecha__date__gte=fecha_inicio_parsed)

    if fecha_fin and fecha_fin != "None":
        fecha_fin_parsed = parse_date(fecha_fin)
        if fecha_fin_parsed:
            compras = compras.filter(compra_fecha__date__lte=fecha_fin_parsed)

    paginator = Paginator(compras, 10)  # 10 compras por página
    page_obj = paginator.get_page(page_number)

    compras_con_items = []
    for compra in page_obj:
        items = producto_compra.objects.filter(compra=compra).select_related('producto')
        compras_con_items.append((compra, items))

    template_path = 'tienda/historial_pdf.html'
    context = {
        'compras_con_items': compras_con_items,
        'cliente': cliente,
    }

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="historial_compras_pagina_{page_obj.number}.pdf"'

    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Hubo un error al generar el PDF.', status=500)
    return response