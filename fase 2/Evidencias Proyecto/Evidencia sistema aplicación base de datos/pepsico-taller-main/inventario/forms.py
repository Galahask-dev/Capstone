# inventario/forms.py
from django import forms
from .models import Repuesto, CategoriaRepuesto, MovimientoInventario, AjusteInventario, PedidoRepuesto

class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = [
            'codigo', 'nombre', 'descripcion', 'categoria', 'marca', 'modelo_compatible',
            'stock_actual', 'stock_minimo', 'stock_maximo', 'precio_costo', 'precio_venta',
            'ubicacion_bodega', 'codigo_barras', 'proveedor', 'tiempo_reposicion'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo_compatible': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_minimo': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_maximo': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'ubicacion_bodega': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'tiempo_reposicion': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class MovimientoInventarioForm(forms.ModelForm):
    class Meta:
        model = MovimientoInventario
        fields = ['repuesto', 'cantidad', 'motivo', 'numero_documento', 'costo_unitario', 'tarea']
        widgets = {
            'repuesto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tarea': forms.Select(attrs={'class': 'form-control'}),
        }

class AjusteInventarioForm(forms.ModelForm):
    class Meta:
        model = AjusteInventario
        fields = ['repuesto', 'cantidad_fisica', 'motivo', 'motivo_otro', 'observaciones', 'fecha_conteo']
        widgets = {
            'repuesto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_fisica': forms.NumberInput(attrs={'class': 'form-control'}),
            'motivo': forms.Select(attrs={'class': 'form-control'}),
            'motivo_otro': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_conteo': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class PedidoRepuestoForm(forms.ModelForm):
    class Meta:
        model = PedidoRepuesto
        fields = ['repuesto', 'cantidad_solicitada', 'proveedor', 'costo_unitario', 'fecha_estimada_entrega', 'observaciones']
        widgets = {
            'repuesto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_solicitada': forms.NumberInput(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
            'costo_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'fecha_estimada_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CategoriaRepuestoForm(forms.ModelForm):
    class Meta:
        model = CategoriaRepuesto
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }