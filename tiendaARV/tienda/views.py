from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Sum, Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from decimal import Decimal

from .models import *
from .forms import *
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView, TemplateView


class welcome(ListView, FormView):
    model = Producto
    template_name = 'tienda/index.html'
    context_object_name = 'productos'
    form_class = FilterForm

    def get_queryset(self):
        queryset = super().get_queryset().order_by('id')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['marcas'] = Marca.objects.all()

        if self.request.user.groups.filter(name='Moderadores').exists():
            context['es_moderador'] = True
        else:
            context['es_moderador'] = False
        return context

    def form_valid(self, form):
        producto_nombre = form.cleaned_data['nombre']
        marca = form.cleaned_data['marca']

        queryset = self.get_queryset().filter(producto_nombre__icontains=producto_nombre)
        if marca:
            queryset = queryset.filter(marca__in=marca)

        self.object_list = queryset
        return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class producto_lista(ListView):
	model = Producto
	template_name = 'tienda/index.html'
	context_object_name = 'productos'


@method_decorator(staff_member_required, name='dispatch')
@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
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
		producto = form.save(commit=False)
		producto.author = self.request.user
		producto.published_date = timezone.now()
		producto.save()
		return redirect('producto_admin')

	def get_object(self, queryset=None):
		pk = self.kwargs.get('pk')
		return get_object_or_404(Producto, pk=pk)


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
            return redirect('verCarrito')
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
		cliente = Cliente(user=user, saldo=0, vip=False, email=user.email, nombre=form.cleaned_data['nombre'],apellidos=form.cleaned_data['apellidos'])
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
        if 'eliminar_compra_id' in request.POST:
            compra_id = request.POST['eliminar_compra_id']
            try:
                compra = Compra.objects.get(pk=compra_id)
                compra.delete()
                messages.success(request, 'La compra ha sido eliminada correctamente.')
            except Compra.DoesNotExist:
                messages.error(request, 'La compra que intenta eliminar no existe.')
            return redirect(request.path)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = get_object_or_404(Cliente, usuario=self.request.user)
        compras = Compra.objects.filter(usuario=cliente)
        compras_con_comentarios = []

        for compra in compras:
            productos_compra = producto_compra.objects.filter(compra=compra)
            comentarios_por_compra = []

            for producto in productos_compra:
                comentarios = Comentario.objects.filter(producto_compra=producto)
                promedio_valoracion = comentarios.aggregate(valoracion_promedio=Avg('valoracion'))['valoracion_promedio']
                comentarios_por_compra.append((producto, comentarios, promedio_valoracion))

            compras_con_comentarios.append((compra, comentarios_por_compra))

        context['compras_con_comentarios'] = compras_con_comentarios
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
        tarjetas_pago = TarjetaPago.objects.filter(cliente=cliente)
        context['cliente'] = cliente
        context['direcciones_envio'] = direcciones_envio
        context['direcciones_facturacion'] = direcciones_facturacion
        context['tarjetas_pago'] = tarjetas_pago
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

		user.email = form.cleaned_data['email']
		user.first_name = form.cleaned_data['nombre']
		user.last_name = form.cleaned_data['apellidos']

		cliente.nombre = form.cleaned_data['nombre']
		cliente.apellidos = form.cleaned_data['apellidos']
		cliente.email = form.cleaned_data['email']

		nueva_contraseña = form.cleaned_data.get('contraseña')
		repetir_contraseña = form.cleaned_data.get('repetir_contraseña')
		nuevo_usuario = form.cleaned_data.get('nuevo_usuario')

		if nueva_contraseña and repetir_contraseña:
			if nueva_contraseña == repetir_contraseña:
				if nueva_contraseña != user.password:
					user.set_password(nueva_contraseña)
					update_session_auth_hash(self.request, user)
			else:
				form.add_error('repetir_contraseña', "Las contraseñas son distintas")
				return self.form_invalid(form)

		if nuevo_usuario:
			if User.objects.filter(username=nuevo_usuario).exists():
				form.add_error('nuevo_usuario', "Este nombre de usuario ya está en uso")
				return self.form_invalid(form)
			else:
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
class tarjeta_new(CreateView):
    model = TarjetaPago
    form_class = EditarTarjetaPagoForm
    template_name = 'tienda/editar_tarjeta.html'
    success_url = reverse_lazy('perfil')

    def form_valid(self, form):
        cliente = self.request.user.cliente
        form.instance.cliente = cliente
        return super().form_valid(form)



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class tarjeta_edit(UpdateView):
    model = TarjetaPago
    form_class = EditarTarjetaPagoForm
    template_name = 'tienda/editar_tarjeta.html'
    success_url = reverse_lazy('perfil')

    def get_object(self, queryset=None):
        cliente = self.request.user.cliente
        tarjeta_pago_id = self.kwargs.get('pk')
        return get_object_or_404(TarjetaPago, id=tarjeta_pago_id, cliente=cliente)

    def form_valid(self, form):
        cliente = self.request.user.cliente
        form.instance.cliente = cliente
        return super().form_valid(form)



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class tarjeta_delete(DetailView):
    model = TarjetaPago
    template_name = 'tienda/eliminar_tarjeta.html'

    def post(self, request, *args, **kwargs):
        tarjeta_pago = get_object_or_404(TarjetaPago, pk=self.kwargs['pk'])
        tarjeta_pago.delete()
        return redirect('perfil')



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class carrito(TemplateView):
    template_name = 'tienda/ver_carrito.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrito = self.request.session.get('carrito', {})
        productos_carrito = []
        total_carrito = 0

        for producto_id, producto_info in carrito.items():
            producto = Producto.objects.get(id=producto_id)
            subtotal_producto = producto_info['precio'] * producto_info['cantidad']
            total_carrito += subtotal_producto
            productos_carrito.append({
                'producto': producto,
                'cantidad': producto_info['cantidad'],
                'subtotal': subtotal_producto
            })

        context['productos_carrito'] = productos_carrito
        context['total_carrito'] = total_carrito
        return context



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class carrito_update(View):
    def post(self, request, *args, **kwargs):
        producto_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad'))

        carrito = request.session.get('carrito', {})
        if producto_id in carrito:
            carrito[producto_id]['cantidad'] = cantidad
            request.session['carrito'] = carrito
            messages.success(request, "La cantidad del producto se actualizó correctamente.")
        else:
            messages.error(request, "El producto no está en el carrito.")

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



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class terminar_compra(View):
    template_name = 'tienda/terminar_compra.html'

    def get(self, request, *args, **kwargs):
        cliente = Cliente.objects.get(usuario=request.user)
        direcciones = Direccion.objects.filter(cliente=cliente)
        tarjetas_pago = TarjetaPago.objects.filter(cliente=cliente)
        context = {
            'direcciones': direcciones,
            'tarjetas_pago': tarjetas_pago,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        direccion_id = request.POST.get('direccion')
        tarjeta_pago_id = request.POST.get('tarjeta_pago')
        carrito = request.session.get('carrito', {})
        total_carrito = sum(Decimal(item['precio']) * item['cantidad'] for item in carrito.values())
        cliente = Cliente.objects.get(usuario=request.user)
        direccion = Direccion.objects.filter(id=direccion_id).first()
        tarjeta_pago = TarjetaPago.objects.filter(id=tarjeta_pago_id).first()

        if direccion and tarjeta_pago:
            if cliente.cliente_saldo >= total_carrito:
                cliente.cliente_saldo -= total_carrito
                cliente.save()

                compra = Compra.objects.create(usuario=cliente, direccion=direccion, metodo_pago=tarjeta_pago, compra_importe=total_carrito)
                for producto_id, item in carrito.items():
                    producto = Producto.objects.get(id=producto_id)
                    producto_compra.objects.create(compra=compra, producto=producto, unidades=item['cantidad'], precio=item['precio'])
                    producto.producto_unidades -= item['cantidad']
                    producto.save()

                del request.session['carrito']
                return redirect('resumenCompra')
            else:
                messages.error(request, "Saldo insuficiente para completar la compra.")
        else:
            messages.error(request, "Por favor, selecciona una dirección y una tarjeta de pago para finalizar la compra.")

        return redirect('finalizarCompra')


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
class comentario_new(CreateView):
    model = Comentario
    form_class = ComentarioForm
    template_name = 'tienda/agregar_comentario.html'

    def form_valid(self, form):
        item_compra_id = self.kwargs['item_compra_id']
        item_compra = get_object_or_404(producto_compra, pk=item_compra_id)
        form.instance.producto_compra = item_compra
        form.instance.user = self.request.user
        form.instance.aprobado = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('informe_compras')

@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class comentario_edit(UpdateView):
    model = Comentario
    form_class = ComentarioForm
    template_name = 'tienda/editar_comentario.html'

    def get_object(self, queryset=None):
        item_id = self.kwargs['item_id']
        comentario = get_object_or_404(Comentario, producto_compra_id=item_id)
        return comentario

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.valoracion = form.cleaned_data['valoracion']
        form.instance.aprobado = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('informe_compras')



@method_decorator(login_required(login_url='/tienda/login/'), name='dispatch')
class comentario_delete(DeleteView):
    model = Comentario
    template_name = 'tienda/comentario_delete.html'
    success_url = reverse_lazy('informe_compras')

    def post(self, request, *args, **kwargs):
        comentario = get_object_or_404(Comentario, id=kwargs['pk'])
        if request.user == comentario.user:
            messages.success(request, "¡Comentario eliminado con éxito!")
            return self.delete(request, *args, **kwargs)
        else:
            messages.error(request, "No tienes permiso para eliminar este comentario.")
            return redirect('informe_compras')


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

