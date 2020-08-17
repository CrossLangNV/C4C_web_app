import logging
import requests
import os

from django.contrib import admin
from django.contrib.auth.models import User

from admin_rest.models import site as rest_site
from scheduler import tasks
from scheduler.tasks import full_service_task, sync_documents_task, score_documents_task, scrape_website_task, parse_content_to_plaintext_task, sync_scrapy_to_solr_task
from .models import Website, Attachment, Document, AcceptanceState, Comment, Tag

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


def full_service(modeladmin, request, queryset):
    for website in queryset:
        full_service_task.delay(website.id)


def scrape_website(modeladmin, request, queryset):
    for website in queryset:
        scrape_website_task.delay(website.id)


def parse_content_to_plaintext(modeladmin, request, queryset):
    for website in queryset:
        parse_content_to_plaintext_task.delay(website.id)


def sync_scrapy_to_solr(modeladmin, request, queryset):
    for website in queryset:
        sync_scrapy_to_solr_task.delay(website.id)


def sync_documents(modeladmin, request, queryset):
    for website in queryset:
        logger.info(website)
        logger.info(website.id)
        sync_documents_task.delay(website.id)


def score_documents(modeladmin, request, queryset):
    for website in queryset:
        score_documents_task.delay(website.id)


def export_documents(modeladmin, request, queryset):
    website_ids = []
    for website in queryset:
        website_ids.append(website.id)
    tasks.export_documents.delay(website_ids)


def extract_terms(modeladmin, request, queryset):
    for website in queryset:
        tasks.extract_terms(website.id)
        logger.info("Done extracting terms!!!!")


def delete_from_solr(modeladmin, requerst, queryset):
    for website in queryset:
        r = requests.post(os.environ['SOLR_URL'] + '/' +
                          'documents' + '/update?commit=true', headers={'Content-Type': 'application/json'}, data='{"delete": {"query": "website:'+website.name.lower()+'"}}')
        logger.info("Deleted solr content for website: %s => %s",
                    website.name.lower(), r.json())


class WebsiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'count_documents']
    ordering = ['name']
    actions = [full_service, scrape_website, sync_scrapy_to_solr, parse_content_to_plaintext,
               sync_documents, score_documents, extract_terms, export_documents, delete_from_solr]

    def count_documents(self, doc):
        return doc.documents.count()

    count_documents.short_description = "Documents"


admin.site.register(Website, WebsiteAdmin)
