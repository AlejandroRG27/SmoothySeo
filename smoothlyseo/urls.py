"""
URL configuration for smoothlyseo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from webapp import views
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('webapp.urls')),  
    path('overview/', views.overview, name='overview'),
    path('caracteristicas/', views.caracteristicas, name='caracteristicas'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('subscription/success/', views.subscription_success, name='subscription_success'),
    path('subscription/cancel/', views.subscription_cancel, name='subscription_cancel'),
    path('manage-subscription/', views.manage_subscription, name='manage_subscription'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('blog/', views.blog, name='blog'),
    path('centro_ayuda/', views.centro_ayuda, name='centro_ayuda'),
    path('quienes-somos/', views.quienes_somos, name='quienes-somos'),
    path('contacto/', views.enviar_contacto, name='contacto'),
    path('logout/', views.signout, name='logout'),
    path('auth/', views.auth_view, name='auth'),
    path('accounts/password/reset/', views.CustomPasswordResetView.as_view(template_name='password_reset.html'), name='account_reset_password'),
    path('accounts/password/reset/done/', views.CustomPasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', views.CustomPasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    path('dashboard/<int:informe_id>/', views.dashboard, name='dashboard'),
    path('download/pdf/<int:informe_id>/', views.download_pdf, name='download_pdf'),
    path('accounts/', include('allauth.urls')),
    path('articulo/nuevo/', views.articulo_nuevo, name='articulo_nuevo'),
    path('aviso-legal/', views.aviso_legal, name='aviso_legal'),
    path('politica-privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('politica-cookies/', views.politica_cookies, name='politica_cookies'),
    path('api/historial/', views.historial_api, name='historial_api'),
    path('api/historial/<str:url>/', views.historial_detail_api, name='historial_detail_api'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'webapp.views.custom_404' 

if settings.DEBUG:
    from django.views.defaults import page_not_found
    urlpatterns += [path('404/', page_not_found, {'exception': Exception()}, name='404')]