# agenda/forms.py
from django import forms
from .models import CitaMantenimiento
from vehiculos.models import Vehiculo

class CitaMantenimientoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['patente'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: ABC123',
            'maxlength': 10,
            'required': True,
        })
        self.fields['fecha_hora'].widget = forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control',
        })
        self.fields['duracion_minutos'].widget = forms.HiddenInput()
        self.fields['tipo_mantencion'].widget = forms.HiddenInput()
        self.fields['observaciones'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3})

    class Meta:
        model = CitaMantenimiento
        fields = ['patente', 'fecha_hora', 'tipo_mantencion', 'duracion_minutos', 'observaciones']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si el usuario es chofer, ofrecer sugerencias de patentes de sus vehículos
        if user and user.rol == 'chofer':
            nombre_chofer = user.get_full_name() or user.username
            vehiculos = Vehiculo.objects.filter(nombre_chofer__icontains=nombre_chofer)
            
            if vehiculos.exists():
                patentes = [(v.patente, f"{v.patente} - {v.marca} {v.modelo}") for v in vehiculos]
                self.fields['patente'].widget = forms.Select(
                    choices=[('', '--- Selecciona o escribe patente ---')] + patentes,
                    attrs={'class': 'form-control'}
                )

        # establecer valor por defecto para tipo_mantencion al ocultarlo
        if 'tipo_mantencion' in self.fields:
            self.fields['tipo_mantencion'].initial = 'otro'
        
    def clean_fecha_hora(self):
        fecha_hora = self.cleaned_data.get('fecha_hora')
        from django.utils import timezone
        if fecha_hora and fecha_hora < timezone.now():
            raise forms.ValidationError("No puedes agendar citas en el pasado.")
        return fecha_hora

    def clean_duracion_minutos(self):
        dur = self.cleaned_data.get('duracion_minutos')
        if not dur or dur <= 0:
            raise forms.ValidationError('La duración estimada es obligatoria.')
        return dur
