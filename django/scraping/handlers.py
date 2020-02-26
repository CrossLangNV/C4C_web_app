import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import urlretrieve, urlopen

from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone

from project import settings
from searchapp.models import Website, EiopaDocument, Attachment


class ScrapingTaskItemHandlerFactory:

    def __init__(self, scraping_item):
        self.scraping_item = scraping_item

    def create_handler(self):
        handler = None
        handler_type = self.scraping_item.task.spider

        if handler_type == 'quotes':
            handler = QuotesItemHandler(self.scraping_item)
        elif handler_type == 'eiopa':
            handler = EiopaItemHandler(self.scraping_item)

        return handler


class ScrapingTaskItemHandler(ABC):

    def __init__(self, scraping_item):
        self.task = scraping_item.task
        self.data = json.loads(scraping_item.data, strict=False)
        self.date = scraping_item.date
        super().__init__()

    @abstractmethod
    def process(self):
        pass


class QuotesItemHandler(ScrapingTaskItemHandler):

    def process(self):
        quote = {
            'text': self.data['text'],
            'author': self.data['author'],
            'tags': self.data['tags']
        }
        # quote.save()
        print("saved quote:")
        print(quote)


class EiopaItemHandler(ScrapingTaskItemHandler):

    def process(self):
        website, created_website = Website.objects.get_or_create(
            name='Eiopa',
            content='Scraped level 3 documents for Eiopa',
            url='https://eiopa.europa.eu'
        )

        document, created_document = EiopaDocument.objects.update_or_create(
            url=self.data['url'],
            defaults={
                'title_prefix': self.data['meta']['title_prefix'],
                'title': self.data['meta']['title'],
                'type': self.data['meta']['type'],
                'date': datetime.strptime(self.data['meta']['date'], '%d %b %Y'),
                'acceptance_state': 'unvalidated',
                'website': website,
                'content': ''.join(self.data['summary'])
            }
        )

        for url in self.data['pdf_docs']:
            file_name = os.path.basename(url)
            response = urlopen(url)
            content = response.read()
            django_file = ContentFile(content)
            attachment, created_attachment = Attachment.objects.get_or_create(
                url=url,
                document=document
            )
            attachment.file.save(file_name, django_file)
