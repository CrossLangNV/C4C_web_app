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


def rdf_get_reports():
    # TODO Mock
    reports = ["report", "submit", "reviewed", "review"]
    return reports


def rdf_get_regulatory_body():
    # TODO Mock
    regulatory_body = ["to the Commission", "to the competent authorities"]
    return regulatory_body


def rdf_get_propmod():
    # TODO Mock
    prop_mod = ["in accordance with the reporting requirements set out in Article 415(1 ) and the uniform reporting formats referred to in Article 415(3 )", "in accordance with requirements"]
    return prop_mod


def rdf_get_entity():
    # TODO Mock
    entity = ["those draft regulatory technical standards", "inflows from any of the liquid assets reported in accordance with Article 416 other than payments due on the assets that are not reflected in the market value of the asset", "inflows from any new obligations entered into", "about the result of the process referred to in Article 20(1)(b )", "Fulfilment of the conditions for such higher inflows"]
    return entity


def rdf_get_frequency():
    # TODO Mock
    frequency = ["regularly", "by 1 January 2015", "daily", "monthly", "yearly"]
    return frequency