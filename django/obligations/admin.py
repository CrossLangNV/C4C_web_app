from django.contrib import admin

# Register your models here.
from obligations.models import ReportingObligation, Comment, Tag, AcceptanceState

admin.site.register(AcceptanceState)
admin.site.register(Comment)
admin.site.register(Tag)

class ReportingObligationAdmin(admin.ModelAdmin):
    actions = ['delete_all_reporting_obligations']

    def delete_all_reporting_obligations(self, request, queryset):
        ReportingObligation.objects.all().delete()


admin.site.register(ReportingObligation, ReportingObligationAdmin)
