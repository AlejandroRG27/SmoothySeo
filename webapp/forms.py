from django import forms
from django.contrib.auth.forms import UserCreationForm
from webapp.models import Usuario, Subscricion, Plan
from django.conf import settings
import stripe

class InformeForm(forms.Form):
    url = forms.CharField(label='URL a analizar', required=True, help_text='Introduce la URL o dominio (ej.: as.com o https://as.com)')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            subscription = Subscricion.objects.filter(usuario=user).first()
            self.plan_name = subscription.plan.nome.lower() if subscription else 'free'

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            subscription = Subscricion.objects.filter(usuario=self.user).first()
            if subscription:
                plan_name = self.plan_name
                consulta_limits = {'free': 1, 'estandar': 5, 'pro': float('inf')}
                if subscription.consultas_diarias >= consulta_limits.get(plan_name, 1):
                    raise forms.ValidationError(f'Has alcanzado el límite de consultas diarias para el plan {plan_name.title()}.')
        return cleaned_data

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if not url:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        if not any(url.startswith(proto) for proto in ['http://', 'https://']):
            url = f'https://{url}'  
        
        return url

class CustomUserCreationForm(UserCreationForm):
    terms = forms.BooleanField(
        label='Acepto los términos y servicios',
        required=True,
        help_text='Debes aceptar los términos y servicios para registrarte.'
    )
    promotions = forms.BooleanField(
        label='Acepto recibir correos promocionales',
        required=False,
        help_text='Opcional: recibirás ofertas y novedades.'
    )

    class Meta:
        model = Usuario
        fields = ['email', 'password1', 'password2', 'terms', 'promotions']  # Elimina 'username'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email ya está registrado.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('terms'):
            raise forms.ValidationError("Debes aceptar los términos y servicios.")
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email  # Asigna email como username
        user.tipo_usuario = 'free'
        if commit:
            user.save()
            free_plan, created = Plan.objects.get_or_create(
                nome='Free',
                defaults={'prezo': 0.00, 'descricion': 'Plan gratuito con análisis ilimitados'}
            )
            try:
                stripe.api_key = settings.STRIPE_API_KEY
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={'user_id': user.id}
                )
                stripe_subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': settings.STRIPE_PRICE_FREE}],
                    metadata={'user_id': user.id}
                )
                subscription = Subscricion.objects.create(
                    usuario=user,
                    plan=free_plan,
                    stripe_customer_id=customer.id,
                    stripe_subscription_id=stripe_subscription.id
                )
                subscription.save()
            except stripe.error.InvalidRequestError as e:
                raise forms.ValidationError(f"Error al crear la suscripción con Stripe: {str(e)}")
            except stripe.error.StripeError as e:
                raise forms.ValidationError(f"Error inesperado con Stripe: {str(e)}")
            except Exception as e:
                raise forms.ValidationError(f"Error inesperado al guardar: {str(e)}")
        return user