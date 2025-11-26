# vehiculos/forms.py
from django import forms
from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'patente', 'tipo_vehiculo', 'marca', 'modelo', 'año',
            'numero_chasis', 'kilometraje', 'nombre_chofer', 
            'telefono_chofer', 'empresa_chofer', 'motivo_ingreso',
            'observaciones_ingreso'
        ]
        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: AB123CD'}),
            'tipo_vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            'numero_chasis': forms.TextInput(attrs={'class': 'form-control'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control'}),
            'nombre_chofer': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_chofer': forms.TextInput(attrs={'class': 'form-control'}),
            'empresa_chofer': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo_ingreso': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones_ingreso': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
# vehiculos/forms.py
from django import forms
from .models import Vehiculo, DocumentoVehiculo, Siniestro, FotoSiniestro


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'patente', 'tipo_vehiculo', 'marca', 'modelo', 'año', 'flota',
            'numero_chasis', 'kilometraje', 'activo', 'nombre_chofer',
            'telefono_chofer', 'empresa_chofer', 'motivo_ingreso',
            'observaciones_ingreso'
        ]
        widgets = {
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: AB123CD'}),
            'tipo_vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Chevrolet'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: N300'}),
            'año': forms.NumberInput(attrs={'class': 'form-control'}),
            'flota': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: FLOTA SUC STA MARTA'}),
            'numero_chasis': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 8LZ1234567890'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 120000'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nombre_chofer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre y Apellido'}),
            'telefono_chofer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 9XXXXXXXX'}),
            'empresa_chofer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: PepsiCo Chile'}),
            'motivo_ingreso': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones_ingreso': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DocumentoVehiculoForm(forms.ModelForm):
    class Meta:
        model = DocumentoVehiculo
        fields = [
            'vehiculo', 'tipo_documento', 'archivo',
            'nombre_archivo', 'descripcion', 'fecha_vencimiento'
        ]
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'archivo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'nombre_archivo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        fields = [
            'vehiculo', 'numero_siniestro', 'descripcion',
            'fecha_siniestro', 'lugar_siniestro', 'estado',
            'compañia_seguro', 'numero_poliza'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_siniestro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'lugar_siniestro': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'compañia_seguro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_poliza': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FotoSiniestroForm(forms.ModelForm):
    class Meta:
        model = FotoSiniestro
        fields = ['siniestro', 'imagen', 'descripcion']
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Formularios para Control de Acceso Vehicular (Guardia)
class RegistroEntradaForm(forms.Form):
    """Formulario para registrar la entrada de un vehículo al taller"""
    patente = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: AB123CD',
            'style': 'text-transform: uppercase;'
        }),
        label='Patente del Vehículo'
    )
    nombre_chofer = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del chofer'
        }),
        label='Nombre del Chofer'
    )
    telefono_chofer = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: +56912345678'
        }),
        label='Teléfono del Chofer'
    )
    empresa_chofer = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: PepsiCo Chile'
        }),
        label='Empresa'
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre el estado del vehículo, daños visibles, etc.'
        }),
        label='Observaciones'
    )
    foto_vehiculo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Foto del Vehículo (Opcional)'
    )



class RegistroSalidaForm(forms.Form):
    """Formulario para registrar la salida de un vehículo del taller"""
    nombre_chofer = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del chofer que retira'
        }),
        label='Nombre del Chofer'
    )
    telefono_chofer = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: +56912345678'
        }),
        label='Teléfono del Chofer'
    )
    kilometraje = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kilometraje al salir'
        }),
        label='Kilometraje de Salida'
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones sobre la entrega del vehículo'
        }),
        label='Observaciones'
    )
    foto_vehiculo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Foto del Vehículo al Salir (Opcional)'
    )

