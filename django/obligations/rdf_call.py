from SPARQLWrapper import SPARQLWrapper, JSON
import json
import logging as logger
import os

from obligations.models import ReportingObligation


def rdf_search(dataset="", subject=None, predicate=None, obj=None):
    if subject is None:
        _subject = '?s'
    else:
        _subject = f'<{subject}>'

    if predicate is None:
        _predicate = '?s'
    else:
        _predicate = f'<{predicate}>'

    if obj is None:
        _obj = '?s'
    else:
        _obj = f'<{obj}>'

    # same for pred and obj
    sparql = SPARQLWrapper(os.environ['RDF_URL']+"/"+dataset)
    q = f"""SELECT {_subject} {_predicate} {_obj}
        WHERE {{
           {_subject} {_predicate} {_obj}
        }}
        LIMIT 25"""
    sparql.setQuery(q)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    logger.info(results)
    return results


def rdf_get_reporters():
    # TODO Mock
    reporters = ReportingObligation.objects.all()
    result = []

    for reporter in reporters:
        logger.info(reporter.name)
        result.append(reporter.name)

    return result


def rdf_get_verbs():
    # TODO Mock
    verbs = ["shall", "must"]

    return verbs