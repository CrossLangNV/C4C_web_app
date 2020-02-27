from django.contrib import admin

from .models import Website, EiopaDocument, Attachment, Document

admin.site.register(Website)
admin.site.register(Document)
admin.site.register(EiopaDocument)
admin.site.register(Attachment)
