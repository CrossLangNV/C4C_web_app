import json
from abc import ABC, abstractmethod
from datetime import datetime

from searchapp.models import Website, Document


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
        Document.objects.update_or_create(
            title=self.data['meta']['title'],
            date=datetime.strptime(self.data['meta']['date'], '%d %b %Y'),
            acceptance_state='unvalidated',
            url=self.data['url'],
            website=website,
            content=''.join(self.data['summary'])
        )
