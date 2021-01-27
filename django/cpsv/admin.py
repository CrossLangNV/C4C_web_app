from django.contrib import admin

# Register your models here.
from cpsv.models import PublicService, PublicServiceConcept, ContactPoint

admin.site.register(PublicService)
admin.site.register(PublicServiceConcept)
admin.site.register(ContactPoint)