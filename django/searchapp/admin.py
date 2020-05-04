from django.contrib import admin
from django.contrib.auth.models import User

from admin_rest.models import site as rest_site
from .tasks import sync_documents_task, score_documents_task, sync_attachments_task

from .models import Website, Attachment, Document, AcceptanceState, Comment, Tag

import logging

logger = logging.getLogger(__name__)

admin.site.register(Document)
admin.site.register(Attachment)
admin.site.register(AcceptanceState)
admin.site.register(Comment)
admin.site.register(Tag)

rest_site.register(Website)
rest_site.register(Document)
rest_site.register(Attachment)
rest_site.register(AcceptanceState)
rest_site.register(Comment)
rest_site.register(Tag)

rest_site.register(User)


def sync_documents(modeladmin, request, queryset):
    for website in queryset:
        logger.info(website)
        logger.info(website.id)
        sync_documents_task(website.id)


def score_documents(modeladmin, request, queryset):
    for website in queryset:
        score_documents_task(website.id)


def sync_attachments(modeladmin, request, queryset):
    for website in queryset:
        sync_attachments_task(website.id)


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'count_documents']
    ordering = ['name']
    actions = [sync_documents, score_documents, sync_attachments]

    def count_documents(self, doc):
        return doc.documents.count()
    count_documents.short_description = "Documents"


admin.site.register(Website, WebsiteAdmin)
