from django.apps import AppConfig
from django.db.models.signals import pre_save
import uuid


class SearchAppConfig(AppConfig):
    name = 'searchapp'

    def ready(self):
        from .signals import pre_save_document
        pre_save.connect(pre_save_document, sender=AppConfig.get_model(self, model_name='Document'),
                         dispatch_uid=str(uuid.uuid4()))
