from django.db.models.signals import post_save
from django.dispatch import receiver

from scraping.handlers import QuotesItemHandler, ScrapyItemHandlerFactory
from scraping.models import ScrapyItem


@receiver(post_save, sender=ScrapyItem)
def postprocess_scrapy_item(sender, instance, created, **kwargs):
    if created:
        print("Saved scrapy item from spider: " + instance.spider)
        # give SrapyItem instance to handler
        factory = ScrapyItemHandlerFactory(instance)
        handler = factory.create_handler()
        handler.process()