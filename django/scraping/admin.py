from django.contrib import admin
from admin_rest.models import site as rest_site
from .models import ScrapingTask, ScrapingTaskItem

admin.site.register(ScrapingTask)
admin.site.register(ScrapingTaskItem)

rest_site.register(ScrapingTask)
rest_site.register(ScrapingTaskItem)