from SPARQLWrapper import SPARQLWrapper, JSON
import json
import logging as logger
import os

from obligations.models import ReportingObligation

def rdf_search(dataset="", subject="", predicate="", obj=""):
    sparql = SPARQLWrapper(os.environ['RDF_URL']+"/"+dataset)

    # TODO Change/update the query
    sparql.setQuery("""
        SELECT ?subject ?predicate ?object
        WHERE {
           ?subject ?predicate ?object
        }
        LIMIT 25
    """)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    logger.info(results)
    return results


def rdf_get_reporters_mock():
    reporters = ReportingObligation.objects.all()
    result = []

    for reporter in reporters:
        logger.info(reporter.name)
        result.append(reporter.name)

    return result