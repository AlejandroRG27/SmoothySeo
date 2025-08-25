from allauth.account.adapter import DefaultAccountAdapter
from .models import Usuario
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # Obtiene el parámetro next de la URL o usa /overview/ por defecto
        next_url = request.GET.get('next', '/overview/')
        return next_url if next_url.startswith('/') else '/overview/'

    def save_user(self, request, form, commit=True):
        user = super().save_user(request, form, commit=False)
        user.email = user.email.lower()
        if 'sociallogin' in request.session:
            social_data = request.session['sociallogin'].account.extra_data
            user = Usuario.create_from_social(social_data)
        if commit:
            user.save()
        return user