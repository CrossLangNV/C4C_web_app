from django.contrib import admin

from .models import Website, Attachment, Document, AcceptanceState

admin.site.register(Website)
admin.site.register(Document)
admin.site.register(Attachment)
admin.site.register(AcceptanceState)