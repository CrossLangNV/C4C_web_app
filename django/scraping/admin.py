from django.contrib import admin
from .models import ScrapingTask, ScrapingTaskItem

admin.site.register(ScrapingTask)
admin.site.register(ScrapingTaskItem)
