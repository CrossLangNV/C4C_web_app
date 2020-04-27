import logging

from django.db.models.signals import post_delete
from django.dispatch import receiver

from searchapp.models import Document, Attachment
from searchapp.solr_call import solr_delete


@receiver(post_delete, sender=Document)
def delete_doc_from_solr(sender, instance, **kwargs):
    logging.info('SIGNAL delete_doc_from_solr')
    solr_delete(core='documents', id=str(instance.id))


@receiver(post_delete, sender=Attachment)
def delete_file_from_solr(sender, instance, **kwargs):
    logging.info('SIGNAL delete_file_from_solr')
    solr_delete(core='files', id=str(instance.id))
