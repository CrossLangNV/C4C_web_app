from django.contrib import admin
from .models import Website, EiopaDocument, Attachment

admin.site.register(Website)
admin.site.register(EiopaDocument)
admin.site.register(Attachment)