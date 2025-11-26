# vehiculos/forms_documentos.py
from django import forms
from .models import DocumentoVehiculo, Siniestro, FotoSiniestro
import os

class DocumentoVehiculoForm(forms.ModelForm):
    class Meta:
        model = DocumentoVehiculo
        fields = ['tipo_documento', 'archivo', 'descripcion', 'fecha_vencimiento']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-control'}),
            'archivo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx,.txt'
            }),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_vencimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            # Validar tamaño del archivo (máximo 10MB)
            if archivo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensión del archivo
            ext = os.path.splitext(archivo.name)[1].lower()
            extensiones_validas = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.txt']
            if ext not in extensiones_validas:
                raise forms.ValidationError(f'Tipo de archivo no válido. Extensiones permitidas: {", ".join(extensiones_validas)}')
        
        return archivo

class SiniestroForm(forms.ModelForm):
    class Meta:
        model = Siniestro
        fields = ['descripcion', 'fecha_siniestro', 'lugar_siniestro', 'compañia_seguro', 'numero_poliza']
        widgets = {
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'fecha_siniestro': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'lugar_siniestro': forms.TextInput(attrs={'class': 'form-control'}),
            'compañia_seguro': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_poliza': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FotoSiniestroForm(forms.ModelForm):
    class Meta:
        model = FotoSiniestro
        fields = ['imagen', 'descripcion']
        widgets = {
            'imagen': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }