from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session

from .solr_call import solr_add


def pre_save_document(sender, instance, **kwargs):
    if sender in [LogEntry, Session]:
        return
    else:
        content = instance.content
        doc_id = instance.id
        # add and index content to Solr
        solr_doc = {
            "id": str(doc_id),
            "content": [content]
        }
        print(content)
        solr_add(core="documents", docs=[solr_doc])
        # clear document content so it doesn't get saved to postgres
        instance.content = ''
