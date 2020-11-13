from django.contrib import admin

from glossary.models import Concept, Comment, Tag, AcceptanceState

admin.site.register(AcceptanceState)
admin.site.register(Comment)
admin.site.register(Tag)

class ConceptAdmin(admin.ModelAdmin):
    actions = ['delete_all_concepts']

    def delete_all_concepts(self, request, queryset):
        Concept.objects.all().delete()

admin.site.register(Concept, ConceptAdmin)