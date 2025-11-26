from .models import Notificacion

def notificaciones(request):
    if request.user.is_authenticated:
        notificaciones_no_leidas = Notificacion.objects.filter(usuario=request.user, leido=False).order_by('-fecha_creacion')
        return {'notificaciones_no_leidas': notificaciones_no_leidas}
    return {}
