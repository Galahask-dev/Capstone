# mantenimientos/forms.py
from django import forms
from .models import Tarea, Pausa

class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['vehiculo', 'titulo', 'descripcion', 'prioridad', 'mecanico_asignado', 'tiempo_estimado']
        widgets = {
            'vehiculo': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'mecanico_asignado': forms.Select(attrs={'class': 'form-control'}),
            'tiempo_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PausaForm(forms.ModelForm):
    class Meta:
        model = Pausa
        fields = ['motivo', 'motivo_otro', 'observaciones']
        widgets = {
            'motivo': forms.Select(attrs={'class': 'form-control'}),
            'motivo_otro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Especificar otro motivo'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CompletarTareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = ['repuestos_utilizados_desc', 'observaciones_finales']
        widgets = {
            'repuestos_utilizados_desc': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Lista de repuestos utilizados en esta tarea...'
            }),
            'observaciones_finales': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Observaciones finales del trabajo realizado...'
            }),
        }