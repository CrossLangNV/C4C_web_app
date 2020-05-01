from django.contrib import admin
from admin_rest.models import site as rest_site
from .models import ScrapingTask

admin.site.register(ScrapingTask)

rest_site.register(ScrapingTask)
