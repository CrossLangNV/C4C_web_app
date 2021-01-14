from django.contrib import admin

from glossary.models import Concept, Comment, Tag, AcceptanceState, AnnotationWorklog

admin.site.register(AcceptanceState)
admin.site.register(Comment)
admin.site.register(Tag)
admin.site.register(AnnotationWorklog)


class ConceptAdmin(admin.ModelAdmin):
    actions = ['delete_all_concepts', 'delete_all_annotationworklogs']
    search_fields = ['id', 'name']
    list_filter = ('website__name', 'version')

    def delete_all_concepts(self, request, queryset):
        Concept.objects.all().delete()

    def delete_all_annotationworklogs(self, request, queryset):
        AnnotationWorklog.objects.all().delete()


admin.site.register(Concept, ConceptAdmin)
