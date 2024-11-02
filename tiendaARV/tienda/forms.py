from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import *
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, ValidationError
from django.contrib.auth.models import User
import re

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
    nombre = forms.CharField(max_length=50)
    apellidos = forms.CharField(max_length=50)

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
        fields = ['calle', 'ciudad', 'codigo_postal', 'pais', 'tipo']
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
class TarjetaPagoForm(forms.ModelForm):
    class Meta:
        model = TarjetaPago
        fields = ['nombre', 'tipo', 'titular', 'caducidad']

class EditarDatosForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)
    repetir_contraseña = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)
    nuevo_usuario = forms.CharField(max_length=150, required=False, label='Nuevo nombre de usuario')

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if not nombre.replace(" ", "").isalpha():
            raise ValidationError("El nombre solo puede contener letras.")
        return nombre

    def clean_apellidos(self):
        apellidos = self.cleaned_data['apellidos']
        if not apellidos.replace(" ", "").isalpha():
            raise ValidationError("Los apellidos solo pueden contener letras.")
        return apellidos

    def clean(self):
        cleaned_data = super().clean()
        contraseña = cleaned_data.get("contraseña")
        contraseña2 = cleaned_data.get("repetir_contraseña")

        if (contraseña and not contraseña2) or (contraseña2 and not contraseña):
            raise ValidationError("Ambas contraseñas tienen que estar rellenas.")

        nueva_contraseña = cleaned_data.get("contraseña")
        contraseña2 = cleaned_data.get("repetir_contraseña")
        nombre = cleaned_data.get("nombre")
        apellidos = cleaned_data.get("apellidos")

        if nueva_contraseña and contraseña2:
            try:
                validate_password(nueva_contraseña)
            except ValidationError as e:
                self.add_error('contraseña', e)
                return cleaned_data

            if nueva_contraseña.lower() in nombre.lower() or nueva_contraseña.lower() in apellidos.lower():
                raise ValidationError("La contraseña no puede parecerse al nombre y/o apellido")

            user = self.instance.usuario
            if user.check_password(nueva_contraseña):
                raise ValidationError("La nueva contraseña no puede ser igual a la anterior")

        return cleaned_data

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellidos', 'email', 'nuevo_usuario', 'contraseña', 'repetir_contraseña']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['apellidos'].required = True
        self.fields['email'].required = True

class ComentarioForm(forms.ModelForm):
    VALORACIONES_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )
    valoracion = forms.ChoiceField(label='Valoración', choices=VALORACIONES_CHOICES)

    class Meta:
        model = Comentario
        fields = ['comentario', 'valoracion']


class EditarTarjetaPagoForm(forms.ModelForm):
    class Meta:
        model = TarjetaPago
        fields = ['nombre', 'tipo', 'titular', 'caducidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].label = 'ID:'
        self.fields['caducidad'].label = 'Caducidad (DD/MM/AAAA):'

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        if len(nombre) != 16 or not nombre.isdigit():
            raise ValidationError('El campo Nombre/ID de la tarjeta debe contener exactamente 16 caracteres numéricos.')
        return nombre

    def clean_titular(self):
        titular = self.cleaned_data['titular']
        if any(char.isdigit() for char in titular):
            raise ValidationError('El campo Titular de la tarjeta no puede contener números.')
        return titular

    def clean_caducidad(self):
        caducidad = self.cleaned_data['caducidad']
        if caducidad < timezone.now().date():
            raise ValidationError('La fecha de caducidad no puede ser anterior a la fecha actual.')
        return caducidad


class AgregarProductoForm(forms.Form):
    cantidad = forms.IntegerField(label='Cantidad', min_value=1)