# Instrucciones para instalar y ejecutar la aplicación Django

## Requisitos previos
- **Python 3.8+**: Descargar e instalar desde [python.org](https://www.python.org/downloads/).
- Asegúrate de que `python` y `pip` estén en el PATH del sistema.

## Pasos para instalar y ejecutar

1. **Descargar el proyecto**
   - Abre una terminal en la carpeta del proyecto (mejor desde el visual directamente).

2. **Ejecuta un entorno virtual**
    - python -m venv venv

**Alternativa**. **Instalar Docker**
    - Descarga e instala docker
    - En el directorio principal ejecuta "docker compose up -d"

3. **Crea archivo .env**
    - Se necesita crear un archivo .env con las APIS necesarias

4. **API's necesarias para ejecutar el proyecto**
    - SECRET_KEY
    - WOORANK_API_KEY
    - DEEPSEEK_API_KEY
    - STRIPE_API_KEY
    - STRIPE_PUBLIC_KEY
    - STRIPE_PRICE_FREE
    - STRIPE_PRICE_STANDARD
    - STRIPE_PRICE_PRO
    - STRIPE_WEBHOOK_SECRET
    - EMAIL_HOST_PASSWORD
    - DOMAIN
    - PGHOST
    - PGPORT
    - PGUSER=
    - PGPASSWORD
    - PGDATABASE
    - GOOGLE_CLIENT_ID
    - GOOGLE_CLIENT_SECRET
    - DEBUG
    - CLIENT_ID
    - SECRET

5. **Configurar la base de datos**
    - Descarga postgreSQL
    - Descarga un gestor de BBDD para postgre (pgAdmin 4)
    - Crea una BBDD llamada "smoothlyseo2_db"
    - Configura settings.py el nombre de ususario y pass
    # Database
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'smoothlyseo2_db',
                'USER': '********',  -> **Aquí nombre de usuario**
                'PASSWORD': '********', -> **Aquí pass de usuario**
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }

6. **Una vez creada y configurada la BBDD tenemos que realizar las migraciones**
    - python manage.py makemigrations
    - python manage.py migrate

7. **Crear super usuario para acceder al panel de administración**
 - python manage.py createsuperuser

8. **Ejecutamos servidor**
    - python manage.py runserver

9. **Accedemos al panel de administración**
    - 127.0.0.1:8000/admin

9. **Configurar los planes en el panel de administrador**
    - Añadir Plans
    - Free, standard y PRO

10. **En subscripciones, asigna PRO al super user para poder realizar varias consultas**

11. **Ya podemos acceder a la aplicación y manejarla correctamente**
