from django.apps import AppConfig


class ScrapingConfig(AppConfig):
    name = 'scraping'

    def ready(self):
        import scraping.signals
