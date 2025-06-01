from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import *
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, ValidationError
from django.contrib.auth.models import User
import re
from captcha.fields import CaptchaField

class ProductoForm(forms.ModelForm):

    class Meta:
        model = Producto
        fields = ('__all__')

class CompraForm(forms.ModelForm):

    class Meta:
        model = Compra
        fields = []

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Usuario", }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contraseña", }), label="Contraseña")
    next = forms.CharField(widget=forms.HiddenInput, initial="/")

class SignInForm(UserCreationForm):
    nombre = forms.CharField(max_length=50, required=True)  # Hacer que el nombre sea obligatorio
    apellidos = forms.CharField(max_length=50, required=True)  # Hacer que los apellidos sean obligatorios
    email = forms.EmailField(required=True)  # Correo obligatorio

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if not nombre.replace(" ", "").isalpha():
            raise forms.ValidationError("El nombre solo puede contener letras")
        return nombre

    def clean_apellidos(self):
        apellidos = self.cleaned_data['apellidos']
        if not apellidos.replace(" ", "").isalpha():
            raise forms.ValidationError("El apellido solo puede contener letras")
        return apellidos

    class Meta:
        model = User
        fields = ['nombre', 'apellidos', 'username', 'email', 'password1', 'password2']


class FilterForm(forms.Form):
    nombre = forms.CharField(required=False, widget=forms.TextInput({"placeholder": "Buscar"}))
    marca = forms.ModelMultipleChoiceField(queryset=Marca.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)


class DireccionForm(forms.ModelForm):
    class Meta:
        model = Direccion
        fields = ['calle', 'ciudad', 'codigo_postal', 'pais']
        labels = {
            'calle': 'Dirección y número:',
            'ciudad': 'Ciudad:',
            'codigo_postal': 'Codigo postal:',
            'pais': 'Pais:',
        }
        widgets = {
            'codigo_postal': forms.TextInput(attrs={'pattern': '\d{5}', 'title': 'El código postal debe contener 5 dígitos numéricos.'}),
        }

    def clean_codigo_postal(self):
        codigo_postal = self.cleaned_data['codigo_postal']
        if not re.match(r'^\d{5}$', codigo_postal):
            raise forms.ValidationError('El código postal debe contener 5 dígitos numéricos.')
        return codigo_postal

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data
    

class EditarDatosForm(forms.ModelForm):
    nuevo_usuario = forms.CharField(
        max_length=150, 
        required=False, 
        label='Nuevo nombre de usuario',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellidos', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')  
        if not nombre:  
            raise ValidationError("El nombre no puede estar vacío.")
        if not nombre.replace(" ", "").isalpha():
            raise ValidationError("El nombre solo puede contener letras.")
        return nombre

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos')  
        if not apellidos:  
            raise ValidationError("Los apellidos no pueden estar vacíos.")
        if not apellidos.replace(" ", "").isalpha():
            raise ValidationError("Los apellidos solo pueden contener letras.")
        return apellidos

    def clean_nuevo_usuario(self):
        nuevo_usuario = self.cleaned_data.get('nuevo_usuario')
        if nuevo_usuario and User.objects.filter(username=nuevo_usuario).exists():
            raise ValidationError("Este nombre de usuario ya está en uso.")
        return nuevo_usuario


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['comentario', 'valoracion']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'valoracion': forms.Select(attrs={'class': 'form-control w-25'}, choices=[
                (5, '★★★★★ - Excelente'),
                (4, '★★★★☆ - Muy bueno'),
                (3, '★★★☆☆ - Bueno'),
                (2, '★★☆☆☆ - Regular'),
                (1, '★☆☆☆☆ - Malo'),
            ]),
        }


# class EditarTarjetaPagoForm(forms.ModelForm):
#     class Meta:
#         model = TarjetaPago
#         fields = ['nombre', 'tipo', 'titular', 'caducidad']

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['nombre'].label = 'ID:'
#         self.fields['caducidad'].label = 'Caducidad (DD/MM/AAAA):'

#     def clean_nombre(self):
#         nombre = self.cleaned_data['nombre']
#         if len(nombre) != 16 or not nombre.isdigit():
#             raise ValidationError('El campo Nombre/ID de la tarjeta debe contener exactamente 16 caracteres numéricos.')
#         return nombre

#     def clean_titular(self):
#         titular = self.cleaned_data['titular']
#         if any(char.isdigit() for char in titular):
#             raise ValidationError('El campo Titular de la tarjeta no puede contener números.')
#         return titular

#     def clean_caducidad(self):
#         caducidad = self.cleaned_data['caducidad']
#         if caducidad < timezone.now().date():
#             raise ValidationError('La fecha de caducidad no puede ser anterior a la fecha actual.')
#         return caducidad


class AgregarProductoForm(forms.Form):
    cantidad = forms.IntegerField(label='Cantidad', min_value=1)

class RecuperarContrasenaForm(forms.Form):
    username = forms.CharField(label='Nombre de Usuario', max_length=150)
    email = forms.EmailField(label='Correo Electrónico')
    nueva_contrasena = forms.CharField(label='Nueva Contraseña', widget=forms.PasswordInput, required=False)
    captcha = CaptchaField()

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')

        if not User.objects.filter(username=username, email=email).exists():
            raise forms.ValidationError("El nombre de usuario y correo no coinciden con ninguna cuenta.")
        return cleaned_data

class SeleccionarCuentaForm(forms.Form):
    cuenta = forms.ModelChoiceField(queryset=None, label="Selecciona tu cuenta de pago")
    metodo_pago = forms.ChoiceField(
        # choices=[('visa', 'Visa'), ('mastercard', 'MasterCard')],
        label="Método de pago"
    )

    def __init__(self, *args, **kwargs):
        cliente = kwargs.pop('cliente')
        super().__init__(*args, **kwargs)
        self.fields['cuenta'].queryset = CuentaPago.objects.filter(cliente=cliente)  # Carga las cuentas del cliente



# class CrearCuentaForm(forms.ModelForm):
#     class Meta:
#         model = CuentaPago
#         fields = ['nombre_cuenta']

class ResponderComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ['comentario']

class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['marca_nombre']

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']