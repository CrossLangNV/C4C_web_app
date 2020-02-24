from django.db.models.signals import post_save
from django.dispatch import receiver

from scraping.handlers import ScrapingTaskItemHandlerFactory
from scraping.models import ScrapingTaskItem, ScrapingTask


@receiver(post_save, sender=ScrapingTaskItem)
def postprocess_scraping_item(sender, instance, created, **kwargs):
    if created:
        scraping_task = ScrapingTask.objects.get(pk=instance.task.id)
        print("Saved scrapy item from spider: " + scraping_task.spider)
        # give ScrapingTaskItem instance to handler
        factory = ScrapingTaskItemHandlerFactory(instance)
        handler = factory.create_handler()
        handler.process()