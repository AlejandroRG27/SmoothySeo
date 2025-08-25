from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import re
from io import BytesIO
import requests
from django.conf import settings
from .forms import InformeForm, CustomUserCreationForm
from webapp.models import Usuario, Informe, Plan, Subscricion, Articulo
import stripe
from openai import OpenAI
from urllib.parse import urlparse
import logging
from datetime import date, datetime
import json
import time
from django.db import IntegrityError
from allauth.account.auth_backends import AuthenticationBackend
from django.utils import timezone
from django.core.mail import send_mail, EmailMessage
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from datetime import datetime;
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django import forms



# Configurar logging
logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_API_KEY

def extract_domain(url):
    # Si no tiene protocolo, añadir https://
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    parsed_url = urlparse(url)
    domain = parsed_url.netloc or parsed_url.path
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain.strip('/')

# Función centralizada para solicitudes HTTP (soporta URLs incompletas)
def fetch_url(url, method='GET', timeout=20, retries=3, **kwargs):
    # Normalizar URL si no tiene protocolo
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    headers = kwargs.get('headers', {})
    headers['User-Agent'] = headers.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    kwargs['headers'] = headers

    for attempt in range(retries):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            if response.status_code == 403:
                logger.warning(f"403 Forbidden para {url}, intento {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))
                    continue
            logger.error(f"Error en solicitud HTTP para {url}: {str(e)}")
            return None
        except requests.RequestException as e:
            logger.error(f"Error en solicitud HTTP para {url}: {str(e)}")
            return None
    return None

# Vista: Página de inicio
def home(request):
    return render(request, 'home.html')

def auth_view(request):
    next_url = request.GET.get('next', '/overview/')  # Inicializar al inicio
    if request.method == 'POST':
        if 'login' in request.POST:
            email = request.POST.get('email')
            password = request.POST.get('password')
            remember_me = request.POST.get('remember_me') == 'on'
            user = authenticate(request, username=email, password=password, backend='allauth.account.auth_backends.AuthenticationBackend')
            if user is not None:
                login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
                if remember_me:
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)  # 2 semanas
                else:
                    request.session.set_expiry(0)  # Cierra sesión al cerrar el navegador
                next_url = request.POST.get('next', next_url)
                return redirect(next_url)
            else:
                return render(request, 'auth.html', {
                    'login_form': AuthenticationForm(),
                    'signup_form': CustomUserCreationForm(),
                    'error': 'Email o contraseña incorrectos'
                })
        elif 'register' in request.POST:
            form = CustomUserCreationForm(request.POST)
            if form.is_valid():
                try:
                    user = form.save()
                    login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
                    next_url = request.POST.get('next', next_url)
                    return redirect(next_url)
                except IntegrityError:
                    return render(request, 'auth.html', {
                        'login_form': AuthenticationForm(),
                        'signup_form': form,
                        'error': 'El email ya está registrado'
                    })
            else:
                # Depuración: Imprimir errores para diagnóstico
                print("Errores del formulario:", form.errors)
                return render(request, 'auth.html', {
                    'login_form': AuthenticationForm(),
                    'signup_form': form,
                    'error': 'Por favor, corrige los errores del formulario'
                })
    else:
        return render(request, 'auth.html', {
            'login_form': AuthenticationForm(),
            'signup_form': CustomUserCreationForm(),
            'next': next_url
        })
        
# Vista: Cierre de sesión
def signout(request):
    logout(request)
    return redirect('home')

# Vista: Overview (análisis de URL)
@login_required
def overview(request):
    subscription = Subscricion.objects.filter(usuario=request.user).first()
    today = datetime.now().date()

    if not subscription:
        customer = stripe.Customer.create(
            email=request.user.email,
            metadata={'user_id': request.user.id}
        )
        free_plan = Plan.objects.filter(nome__iexact='free').first()
        if not free_plan:
            free_plan = Plan.objects.create(nome='Free', prezo=0.00, descricion='Plan gratuito con 1 consulta diaria', stripe_price_id=settings.STRIPE_PRICE_FREE)
        subscription = Subscricion.objects.create(
            usuario=request.user,
            plan=free_plan,
            stripe_customer_id=customer.id,
            active=True,
            consultas_diarias=0,
            ultima_consulta=today
        )
        stripe_subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': settings.STRIPE_PRICE_FREE}],
            metadata={'user_id': request.user.id}
        )
        subscription.stripe_subscription_id = stripe_subscription.id
        subscription.save()

    if subscription.ultima_consulta != today:
        subscription.consultas_diarias = 0
        subscription.ultima_consulta = today
        subscription.save()

    plan_name = subscription.plan.nome.lower()
    consulta_limits = {'free': 1, 'standard': 5, 'pro': float('inf')}
    if subscription.consultas_diarias >= consulta_limits.get(plan_name, 1):
        return render(request, 'overview.html', {
            'form': InformeForm(user=request.user),
            'error': f'Has alcanzado el límite de consultas diarias para el plan {plan_name.title()}.'
        })

    if request.method == 'POST':
        form = InformeForm(request.POST, user=request.user)
        if form.is_valid():
            url = form.cleaned_data['url']
            domain = extract_domain(url)

            subscription.consultas_diarias += 1
            subscription.save()
            
            try:
                # Agregar timeout a la llamada a WooRank (30 segundos)
                woorank_response = requests.get(
                    'https://api2.woorank.com/reviews',
                    headers={'X-API-KEY': settings.WOORANK_API_KEY},
                    params={'url': domain, 'language': 'es'},
                    timeout=600  # Timeout en segundos para evitar bloqueos
                )
                woorank_response.raise_for_status()
                woorank_data = woorank_response.json()
                puntuacion = woorank_data.get('score', 0)
                screenshot = woorank_data.get('screenshot')
                criteria = woorank_data.get('criteria', {})

                problems = {}
                for crit in criteria.values():
                    name = crit['type'].lower()
                    problems[name] = {
                        'status': crit['status'],
                        'advice': crit['advice'],
                        'data': crit['data'],
                        'solvability': crit['solvability'],
                        'importance': crit['importance']
                    }
            except requests.Timeout:
                logger.error("Timeout en llamada a WooRank API")
                return render(request, 'overview.html', {
                    'form': form,
                    'error': 'La solicitud a WooRank tardó demasiado. Intente más tarde.'
                })
            except Exception as e:
                logger.error(f"Error en WooRank: {str(e)}")
                return render(request, 'overview.html', {
                    'form': form,
                    'error': f'Error al consultar WooRank: {str(e)}'
                })

            try:
                client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
                system_prompt = (
                    "Eres un experto en SEO, rendimiento web y accesibilidad. Tu tarea es analizar un informe SEO generado por WooRank para un sitio web y generar un informe detallado en español, en formato Markdown. "
                    "Para cada problema identificado, proporciona: 1) un análisis breve del impacto en SEO, rendimiento o accesibilidad; 2) una solución personalizada y accionable, considerando el tipo de sitio (por ejemplo, e-commerce, blog, corporativo). "
                    "Prioriza los problemas según su impacto. Si no hay problemas específicos, ofrece recomendaciones generales para mejorar el sitio. "
                    "Crea una sección con 10 palabras clave relacionadas con la temática del sitio. "
                    "Incluye una sección de 'Razonamiento' al final, explicando tu enfoque y decisiones, en español y en Markdown."
                )
                prompt = (
                    f"Analiza el siguiente informe SEO de WooRank para el sitio {url}:\n"
                    f"## Resumen del análisis:\n"
                    f"- Puntuación: {puntuacion}\n"
                    f"## Problemas clave:\n"
                    + '\n'.join([f"- **{name.title()}**: Status: {details['status']}, Advice: {details['advice']}" for name, details in problems.items()])
                    + "\nProporciona un análisis detallado y soluciones personalizadas según las instrucciones."
                )
                # Agregar timeout a la llamada a DeepSeek API (30 segundos)
                response = client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=5000,
                    stream=False,
                    timeout=600  # Timeout en segundos para evitar bloqueos
                )
                full_response = response.choices[0].message.content.strip()
                logger.debug(f"Respuesta completa IA: {full_response}")
                consello_ia = full_response
                razonamiento = ''
                if '## Razonamiento' in full_response:
                    parts = full_response.split('## Razonamiento', 1)
                    consello_ia_lines = [line.strip() for line in parts[0].split('\n') if line.strip()]
                    consello_ia = '\n'.join(consello_ia_lines)
                    razonamiento_lines = [line.strip() for line in parts[1].split('\n') if line.strip()]
                    razonamiento = '## Razonamiento\n' + '\n'.join(razonamiento_lines)
            except TimeoutError:
                logger.error("Timeout en llamada a DeepSeek API")
                consello_ia = 'Error al generar el consejo de IA: Timeout en la solicitud.'
                razonamiento = 'No se pudo obtener razonamiento debido a timeout.'
            except Exception as e:
                logger.error(f"Error al generar consejo de DeepSeek: {str(e)}")
                consello_ia = f'Error al generar el consejo de IA: {str(e)}'
                razonamiento = 'No se pudo obtener razonamiento.'

            informe = Informe(
                usuario=request.user,
                url=url,
                puntuacion=puntuacion,
                screenshot=screenshot,
                problemas=problems,
                consello_ia=consello_ia,
                data=datetime.now(),
                razonamiento=razonamiento
            )
            informe.save()
            return redirect('dashboard', informe_id=informe.id)
        else:
            return render(request, 'overview.html', {
                'form': form,
                'error': 'Introduce una URL válida'
            })
    else:
        form = InformeForm(user=request.user)
        return render(request, 'overview.html', {'form': form})
    
@login_required
def dashboard(request, informe_id):
    informe = get_object_or_404(Informe, id=informe_id, usuario=request.user)
    subscription = get_object_or_404(Subscricion, usuario=request.user)

    informe.puntuacion = int(informe.puntuacion) if isinstance(informe.puntuacion, (int, float)) else 0

    problems = informe.problemas or {}
    
    # Contar problemas por estado
    status_counts = {
        'good': 0,
        'neutral': 0,
        'bad': 0
    }

    for details in problems.values():
        status = details.get('status', 'neutral').lower()
        status_mapping = {
            'good': 'good',
            'average': 'neutral',
            'bad': 'bad',
            'neutral': 'neutral'
        }
        details['status'] = status_mapping.get(status, 'neutral')
        if status in status_counts:
            status_counts[status] += 1

    sections = {
        'On-Page / Content': ['title', 'description', 'google_preview', 'headings', 'keywords_cloud', 'images', 'broken_links', 'links_details', 'language', 'encoding', 'doctype', 'favicon', 'custom_404', 'clean_url', 'underscores_url'],
        'Indexing': ['robots_txt', 'xml_sitemaps', 'sitemaps_validity', 'canonical_tags', 'hreflang', 'robots_tags'],
        'Mobile': ['amp', 'core_web_vitals', 'mobile_compatibility', 'mobile_viewport', 'mobile_fontsize', 'mobile_taptargets', 'mobile_friendliness'],
        'Structured Data': ['schema_org', 'open_graph', 'twitter_card', 'microformats'],
        'Security': ['ssl_secured', 'mixed_content', 'email_security', 'dmarc'],
        'Performance': ['resources_minification', 'resources_compression', 'resources_cacheability', 'image_optimization', 'layout_shift_elements', 'largest_contentful_paint_element'],
        'Accessibility': ['accessibility_contrast', 'accessibility_navigation'],
        'Technologies': ['technologies', 'analytics_technologies'],
        'Branding': ['crunchbase'],
        'Domain': ['domain_registration'],
        'Off-Page': ['backlinks_score', 'backlinks_counter', 'backlinks_ref_domains', 'indexed_pages', 'traffic_estimation'],
        'Social': ['discovered_social_profiles', 'facebook_brand_page', 'instagram', 'linkedin', 'twitter_account', 'shared_count']
    }

    sectioned_problemas = {section: {field: problems.get(field, {'status': 'neutral', 'advice': 'Sin datos disponibles'}) for field in fields} for section, fields in sections.items()}

    chart_data = {
        'woorank': {
            'score': informe.puntuacion,
            'problemas': problems
        }
    }

    return render(request, 'dashboard.html', {
        'informe': informe,
        'subscription': subscription,
        'chart_data_json': json.dumps(chart_data),
        'plan_name': subscription.plan.nome,
        'sectioned_problemas': sectioned_problemas,
        'status_counts': status_counts,
    })

def clean_html_for_reportlab(text):
    """Limpia el texto HTML para hacerlo compatible con ReportLab."""
    if not text:
        return ""
    # Eliminar atributos no soportados como rel="nofollow"
    text = re.sub(r'<a\s+[^>]*rel="[^"]*"[^>]*>', '<a>', text)
    # Reemplazar <br> por saltos de línea
    text = re.sub(r'<br\s*/?>', '\n', text)
    # Quitar etiquetas no soportadas, dejando solo texto y enlaces básicos
    text = re.sub(r'</?[^>]+(?!</a>)(?!<a[^>]*>)>', '', text)
    return text

@login_required
def download_pdf(request, informe_id):
    informe = get_object_or_404(Informe, id=informe_id, usuario=request.user)
    subscription = get_object_or_404(Subscricion, usuario=request.user)

    if subscription.plan.nome.lower() == 'free':
        return HttpResponse("El plan Free no permite descargas en PDF. ¡Suscríbete al plan Standard o Pro!", status=403)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    elements = []

    # Estilos personalizados
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.darkblue,
        spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.black,
        spaceAfter=15
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    problem_style = ParagraphStyle(
        'Problem',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        leftIndent=20,
        spaceAfter=10
    )
    data_style = ParagraphStyle(
        'Data',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=40,
        spaceAfter=5
    )
    # Estilos con colores según estado
    good_style = ParagraphStyle(
        'Good',
        parent=problem_style,
        backColor=colors.green,  # Verde claro transparente (ajustable con alpha)
        backColorAlpha=0.3
    )
    neutral_style = ParagraphStyle(
        'Neutral',
        parent=problem_style,
        backColor=colors.yellow,  # Amarillo claro transparente (ajustable con alpha)
        backColorAlpha=0.3
    )
    bad_style = ParagraphStyle(
        'Bad',
        parent=problem_style,
        backColor=colors.red,  # Rojo claro transparente (ajustable con alpha)
        backColorAlpha=0.3
    )

    # Título del informe
    elements.append(Paragraph(f"Informe SEO para {informe.url}", title_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Plan: {subscription.plan.nome}", subtitle_style))
    elements.append(Paragraph(f"Puntuación: {informe.puntuacion}/100", subtitle_style))
    elements.append(Spacer(1, 20))

    # Sección de Problemas
    elements.append(Paragraph("Problemas Detectados", subtitle_style))
    for name, details in informe.problemas.items():
        # Seleccionar estilo según estado
        style = problem_style
        if 'status' in details:
            status = details['status'].lower()
            if status == 'good':
                style = good_style
            elif status == 'neutral' or status == 'average':
                style = neutral_style
            elif status == 'bad':
                style = bad_style
        text = f"<b>{name.title()}</b>: {clean_html_for_reportlab(details['advice'])}"
        if 'status' in details:
            text += f" (Estado: {details['status']})"
        elements.append(Paragraph(text, style))
        if 'data' in details and details['data']:
            data_text = "<i>Datos:</i><br/>"
            if isinstance(details['data'], dict):
                for key, value in details['data'].items():
                    data_text += f"<b>{key.title()}:</b> {clean_html_for_reportlab(str(value))}<br/>"
            elif isinstance(details['data'], list):
                for item in details['data'][:5]:  # Limitar a 5 elementos
                    data_text += f"- {clean_html_for_reportlab(str(item))}<br/>"
            elements.append(Paragraph(data_text, data_style))
        elements.append(Spacer(1, 10))

    # Sección de Consejo IA
    elements.append(Paragraph("Consejo IA", subtitle_style))
    if informe.consello_ia:
        advice_lines = [line.strip() for line in informe.consello_ia.split('\n') if line.strip()]
        for line in advice_lines:
            elements.append(Paragraph(clean_html_for_reportlab(line), normal_style))
        elements.append(Spacer(1, 20))

    # Sección de Razonamiento
    elements.append(Paragraph("Razonamiento", subtitle_style))
    if informe.razonamiento:
        reasoning_lines = [line.strip() for line in informe.razonamiento.split('\n') if line.strip()]
        for line in reasoning_lines:
            elements.append(Paragraph(clean_html_for_reportlab(line), normal_style))
        elements.append(Spacer(1, 20))

    # Generar el PDF
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="informe_{informe_id}.pdf"'
    return response

# Vistas adicionales
def caracteristicas(request):
    return render(request, 'caracteristicas.html')


def subscribe(request):
    current_plan = None
    error = None
    subscription = None  # Inicializar subscription como None fuera del bloque if
    
    if request.user.is_authenticated:
        try:
            subscription = Subscricion.objects.filter(usuario=request.user).first()
            current_plan = subscription.plan.nome.lower() if subscription and subscription.plan else 'free'
        except Subscricion.DoesNotExist:
            error = "No se encontró una suscripción asociada."
        except Exception as e:
            error = f"Error al cargar el plan: {str(e)}"
    
    return render(request, 'subscribe.html', {
        'current_plan': current_plan,
        'error': error,
        'stripe_public_key': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'subscription': subscription  # subscription puede ser None si no está autenticado
    })

@login_required
def subscription_success(request):
    session_id = request.GET.get('session_id')
    if session_id:
        # Manejo para sesiones de checkout con session_id presente
        try:
            stripe.api_key = settings.STRIPE_API_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            subscription_id = session.subscription
            plan_name = session.metadata.get('plan')
            user_id = session.client_reference_id

            if str(user_id) == str(request.user.id):
                subscription = Subscricion.objects.get(usuario=request.user)
                plan = Plan.objects.filter(nome__iexact=plan_name).first()
                if not plan:
                    price_id = getattr(settings, f'STRIPE_PRICE_{plan_name.upper()}')  # Obtener price_id de settings
                    plan = Plan.objects.create(
                        nome=plan_name.title(),
                        prezo=5.00 if plan_name == 'standard' else 10.00 if plan_name == 'pro' else 0.00,
                        descricion=f'Plan {plan_name.title()} con {"1 consulta diaria" if plan_name == "free" else "5 consultas diarias" if plan_name == "standard" else "consultas ilimitadas"}',
                        stripe_price_id=price_id  # Asignar stripe_price_id para consistencia
                    )
                
                # Corregir modificación de suscripción recuperando ítem real
                if subscription.stripe_subscription_id:
                    stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                    item_id = stripe_sub['items']['data'][0]['id']  # Obtener ID real del ítem
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        items=[{'id': item_id, 'price': getattr(settings, f'STRIPE_PRICE_{plan_name.upper()}')}]
                    )
                else:
                    # Si es nueva, no modificar; solo asignar ID
                    pass

                subscription.plan = plan
                subscription.stripe_subscription_id = subscription_id
                subscription.active = True
                subscription.consultas_diarias = 0
                subscription.ultima_consulta = date.today()
                subscription.save()
                
                # Actualizar tipo_usuario consistentemente
                request.user.tipo_usuario = plan_name
                request.user.save()
                
                return render(request, 'subscription_success.html', {'message': f'Suscripción actualizada a {plan_name.title()}'})
            else:
                return render(request, 'subscription_success.html', {'error': 'ID de usuario no coincide'})
        except stripe.error.StripeError as e:
            return render(request, 'subscription_success.html', {'error': f'Error con Stripe: {str(e)}'})
        except Exception as e:
            return render(request, 'subscription_success.html', {'error': f'Error al procesar: {str(e)}'})
    else:
        # Manejo para retorno del portal sin session_id
        try:
            subscription = Subscricion.objects.get(usuario=request.user)
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
            # Actualizar localmente si es necesario (aunque webhook debería manejarlo)
            if stripe_sub['status'] == 'active':
                # Sincronizar plan, etc., similar al webhook
                new_price_id = stripe_sub['items']['data'][0]['price']['id']
                new_plan = Plan.objects.filter(stripe_price_id=new_price_id).first()
                if new_plan:
                    subscription.plan = new_plan
                    subscription.save()
                    request.user.tipo_usuario = new_plan.nome.lower()
                    request.user.save()
                message = 'Suscripción gestionada exitosamente. Cambios aplicados.'
            else:
                message = 'Suscripción gestionada, pero verifique el estado.'
            return render(request, 'subscription_success.html', {'message': message})
        except Exception as e:
            return render(request, 'subscription_success.html', {'error': f'Error al verificar: {str(e)}'})

def subscription_cancel(request):
    return render(request, 'subscription_cancel.html')

from django.urls import reverse  # Asegúrese de importar reverse si no está presente

@login_required
def manage_subscription(request):
    try:
        subscription = Subscricion.objects.get(usuario=request.user)
        stripe.api_key = settings.STRIPE_API_KEY
        session = stripe.billing_portal.Session.create(
            customer=subscription.stripe_customer_id,
            return_url=request.build_absolute_uri(reverse('subscription_success'))
        )
        return redirect(session.url)
    except Subscricion.DoesNotExist:
        return render(request, 'subscribe.html', {'error': 'No se encontró una suscripción asociada.'})
    except Exception as e:
        return render(request, 'subscribe.html', {'error': f'Error al gestionar la suscripción: {str(e)}'})

def centro_ayuda(request):
    return render(request, 'centro_ayuda.html')

def quienes_somos(request):
    return render(request, 'quienes-somos.html')

def enviar_contacto(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        email = request.POST['email']
        departamento = request.POST['departamento']
        asunto = request.POST['asunto']
        mensaje = request.POST['mensaje']
        
        try:
            # Construir el contenido del email
            email_content = f"De: {nombre} ({email})\nDepartamento: {departamento}\n\n{mensaje}"
            # Usar EmailMessage para más control (opcional)
            email = EmailMessage(
                subject=f'Contacto - {asunto}',
                body=email_content,
                from_email=settings.DEFAULT_FROM_EMAIL,  # Remitente autenticado
                to=['alejandro.rodriguez1900@gmail.com'],  # Destinatario fijo
                reply_to=[email],  # Permite responder al usuario
            )
            email.send(fail_silently=False)
            messages.success(request, 'Tu mensaje ha sido enviado con éxito. Te responderemos pronto.')
        except Exception as e:
            messages.error(request, f'Error al enviar el mensaje: {str(e)}. Inténtalo de nuevo.')
        
        return redirect(reverse('contacto'))
    return render(request, 'contacto.html')

# Para la parte de los blogs
def is_admin(user):
    return user.is_authenticated and user.tipo_usuario == 'admin'


def blog(request):
    articulos = Articulo.objects.all()
    return render(request, 'blog.html', {'articulos': articulos, 'user': request.user})

class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = ['titulo', 'subtitulo', 'cuerpo', 'imagen']

@login_required
@user_passes_test(is_admin)
def articulo_nuevo(request):
    if request.method == 'POST':
        form = ArticuloForm(request.POST, request.FILES)
        if form.is_valid():
            articulo = form.save(commit=False)
            articulo.autor = request.user
            articulo.save()
            logger.debug(f"Imagen subida a: {articulo.imagen.url}")
            return redirect('blog')
        else:
            logger.error(f"Errores de formulario: {form.errors}")
            # Opcional: Mostrar errores en la plantilla
    else:
        form = ArticuloForm()
    return render(request, 'articulo_form.html', {'form': form})

def aviso_legal(request):
    return render(request, 'aviso_legal.html')

def politica_privacidad(request):
    return render(request, 'politica_privacidad.html')

def politica_cookies(request):
    return render(request, 'politica_cookies.html')

def pro_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        user = get_object_or_404(Usuario, id=request.user.id)
        if user.tipo_usuario != 'pro':
            return JsonResponse({'error': 'El historial solo está disponible para usuarios Pro'}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@login_required
@pro_required
def historial_api(request):
    informes = Informe.objects.filter(usuario=request.user).values('id', 'url', 'puntuacion', 'data')
    return JsonResponse(list(informes), safe=False)

@login_required
def historial_detail_api(request, url):
    informe = get_object_or_404(Informe, usuario=request.user, url=url)
    return JsonResponse({'id': informe.id, 'url': informe.url, 'puntuacion': informe.puntuacion, 'data': informe.data})


def custom_404(request, exception):
    return render(request, '404.html', status=404)


User = get_user_model()

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')
    from_email = settings.DEFAULT_FROM_EMAIL

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            self.request.session['reset_user_email'] = email
            logger.debug(f"Intentando enviar correo de restablecimiento a: {email}")
            response = super().form_valid(form)
            logger.debug(f"Correo enviado a: {email}")
            return response
        except User.DoesNotExist:
            messages.error(self.request, 'No existe un usuario con ese email.')
            logger.warning(f"Intento de restablecimiento para email no registrado: {email}")
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error al enviar correo a {email}: {str(e)}")
            messages.error(self.request, 'Error al enviar el correo de restablecimiento. Intenta de nuevo.')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'SmoothlySEO'
        context['domain'] = settings.DOMAIN  # Añadir dominio al contexto
        return context


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'SmoothlySEO'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        messages.success(self.request, 'Tu contraseña ha sido restablecida con éxito.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'SmoothlySEO'
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_name'] = 'SmoothlySEO'
        context['login_url'] = reverse_lazy('auth')
        return context
    
    
    
@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_API_KEY
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Webhook payload inválido: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Firma de webhook inválida: {e}")
        return HttpResponse(status=400)

    # Manejar actualización de suscripción
    if event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        user_id = subscription['metadata'].get('user_id')
        if user_id:
            try:
                user = Usuario.objects.get(id=user_id)
                sub = Subscricion.objects.get(usuario=user, stripe_subscription_id=subscription['id'])
                new_price_id = subscription['items']['data'][0]['price']['id']
                new_plan = Plan.objects.filter(stripe_price_id=new_price_id).first()
                
                # Modificación: Manejar si new_plan no existe
                if not new_plan:
                    logger.error(f"Plan no encontrado para price_id: {new_price_id}. Creando uno genérico.")
                    # Opcional: Crear plan dinámicamente (consultar Stripe para detalles si es necesario)
                    price = stripe.Price.retrieve(new_price_id)
                    new_plan = Plan.objects.create(
                        nome=price['nickname'] or 'Plan Desconocido',
                        prezo=price['unit_amount'] / 100,
                        descricion='Plan creado automáticamente desde webhook',
                        stripe_price_id=new_price_id
                    )
                
                sub.plan = new_plan
                sub.active = (subscription['status'] == 'active')
                sub.save()
                
                # Modificación: Actualizar tipo_usuario en Usuario
                user.tipo_usuario = new_plan.nome.lower()
                user.save()
                
                logger.info(f"Suscripción actualizada para usuario {user_id}: nuevo plan {sub.plan.nome if sub.plan else 'Desconocido'}")
            except Exception as e:
                logger.error(f"Error al procesar actualización de suscripción: {str(e)}")

    # Puedes agregar más eventos, como cancelación
    if event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        user_id = subscription['metadata'].get('user_id')
        if user_id:
            try:
                user = Usuario.objects.get(id=user_id)
                sub = Subscricion.objects.get(usuario=user, stripe_subscription_id=subscription['id'])
                sub.active = False
                sub.save()
                
                # Modificación: Actualizar tipo_usuario a 'free' en cancelación
                user.tipo_usuario = 'free'
                user.save()
                
                logger.info(f"Suscripción cancelada para usuario {user_id}")
            except Exception as e:
                logger.error(f"Error al procesar cancelación de suscripción: {str(e)}")

    return HttpResponse(status=200)

