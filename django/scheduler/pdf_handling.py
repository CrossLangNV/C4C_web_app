import binascii
import logging

from celery import shared_task
from django.apps import apps
from tika import parser

'''
Extract text from pdf, use for Document content
'''


@shared_task
def pdf_extract(pdf_base64, document_id):
    pdf_bytes = binascii.a2b_base64(pdf_base64)
    logging.info('Parsing PDF with tika...')
    pdf_text = parser.from_buffer(pdf_bytes, xmlContent=True)

    Document = apps.get_model('searchapp.Document')
    doc = Document.objects.get(id=document_id)
    doc.content = pdf_text['content']
    doc.extract_text = False
    doc.save()

    return pdf_text['content']