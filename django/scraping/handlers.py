import json
from abc import ABC, abstractmethod
from datetime import datetime

from searchapp.models import Website, Document


class ScrapyItemHandlerFactory:

    def __init__(self, scrapy_item):
        self.scrapy_item = scrapy_item

    def create_handler(self):
        handler = None
        handler_type = self.scrapy_item.spider

        if handler_type == 'quotes':
            handler = QuotesItemHandler(self.scrapy_item)
        elif handler_type == 'eiopa':
            handler = EiopaItemHandler(self.scrapy_item)

        return handler


class ScrapyItemHandler(ABC):

    def __init__(self, scrapy_item):
        self.spider = scrapy_item.spider
        self.data = json.loads(scrapy_item.data, strict=False)
        self.date = scrapy_item.date
        super().__init__()

    @abstractmethod
    def process(self):
        pass


class QuotesItemHandler(ScrapyItemHandler):
    quotes = []

    def process(self):
        for obj in self.data:
            quote = {
                'text': obj['text'],
                'author': obj['author'],
                'tags': obj['tags']
            }
            # quote.save()
            print("saved quote:")
            print(quote)
            self.quotes.append(quote)


class EiopaItemHandler(ScrapyItemHandler):

    def process(self):
        website = Website.objects.create(
            name='Eiopa',
            content='Scraped level 3 documents for Eiopa',
            url='https://eiopa.europa.eu'
        )
        for obj in self.data:
            document = Document.objects.create(
                title=obj['meta']['title'],
                date= datetime.strptime(obj['meta']['date'], '%d %b %Y'),
                acceptance_state='unvalidated',
                url=obj['url'],
                website=website,
                content=''.join(obj['summary'])
            )
