from django.contrib.auth import get_user_model

User = get_user_model()

class ViewAsRoleMiddleware:
	"""Middleware para habilitar "ver como rol".

	Si la sesión contiene 'view_as_role', la middleware marca `request.viewing_as_role`
	y mantiene una referencia en `request.original_user`. También sobrescribe
	temporalmente `request.user.rol` para que las plantillas y vistas respondan
	como si el usuario tuviera ese rol.
	"""
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		request.viewing_as_role = False
		request.original_user = None

		if request.user.is_authenticated:
			# Guardar el rol real del usuario ANTES de cualquier modificación
			original_rol = request.user.rol
			
			view_as = request.session.get('view_as_role')
			if view_as:
				request.viewing_as_role = True
				# Mantener referencia al usuario real para mostrar su nombre
				try:
					request.original_user = User.objects.get(pk=request.session.get('original_user_id') or request.user.id)
				except User.DoesNotExist:
					request.original_user = request.user

				# Cambiar atributo rol del usuario en memoria (no se guarda en DB)
				# Esto afecta sólo a la petición actual y ayuda a evaluar permisos y menús
				request.user.rol = view_as
			else:
				# Asegurar que el rol del usuario es el real (en caso de que se haya limpiado la sesión)
				request.user.refresh_from_db()

		response = self.get_response(request)
		return response

