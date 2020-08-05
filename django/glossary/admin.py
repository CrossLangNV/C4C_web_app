from django.contrib import admin

from glossary.models import Concept, Comment, Tag, AcceptanceState

admin.site.register(AcceptanceState)
admin.site.register(Concept)
admin.site.register(Comment)
admin.site.register(Tag)
