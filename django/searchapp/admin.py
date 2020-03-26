from django.contrib import admin
from django.contrib.auth.models import User

from admin_rest.models import site as rest_site

from .models import Website, Attachment, Document, AcceptanceState

admin.site.register(Website)
admin.site.register(Document)
admin.site.register(Attachment)
admin.site.register(AcceptanceState)

rest_site.register(Website)
rest_site.register(Document)
rest_site.register(Attachment)
rest_site.register(AcceptanceState)

rest_site.register(User)