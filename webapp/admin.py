from django.contrib import admin
from .models import Usuario
from .models import Plan
from .models import Subscricion
from .models import Informe
from .models import Articulo



admin.site.register(Usuario)
admin.site.register(Plan)
admin.site.register(Subscricion)
admin.site.register(Informe)
admin.site.register(Articulo)
