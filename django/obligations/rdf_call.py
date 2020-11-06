from SPARQLWrapper import SPARQLWrapper, JSON
import json
import logging as logger
import os
from typing import List, Tuple


from obligations.models import ReportingObligation
from obligations import build_rdf
from obligations.build_rdf import D_ENTITIES, ExampleCasContent, ROGraph
from obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper, SPARQLGraphWrapper
from obligations.rdf_mock import rdf_get_reporters_mock, rdf_get_verbs_mock, rdf_get_reports_mock,\
    rdf_get_regulatory_body_mock, rdf_get_propmod_mock, rdf_get_entity_mock, rdf_get_frequency_mock

# You might have to change this
URL_FUSEKI = os.environ['RDF_FUSEKI_URL'] + "/reporting_obligations"
graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
ro_provider = SPARQLReportingObligationProvider(graph_wrapper)


def rdf_get_available_entities():
    entities_list = ro_provider.get_different_entities()
    logger.info("entities_list: %s", entities_list)
    return entities_list


def rdf_get_predicate(predicate):
    return ro_provider.get_all_from_type(f"http://dgfisma.com/reporting_obligation#{predicate}")


# Test this in the console
def rdf_get_all_reporting_obligations():
    return ro_provider.get_all_ro_str()


def rdf_query_predicate_single(predicate, query):
    return ro_provider.get_filter_single(f"http://dgfisma.com/reporting_obligation#{predicate}", query)


# Example: rdf_query_predicate([("http://dgfisma.com/reporting_obligation#hasReporter", "by the ECB")])
def rdf_query_predicate(list_pred_value: List[Tuple[str]]):
    return ro_provider.get_filter_multiple(list_pred_value)


# Below feels duplicate, lets rewrite this
def rdf_get_reporters():
    # reporters_list_mock = rdf_get_reporters_mock()
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasReporter")


def rdf_get_verbs():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasVerb")


def rdf_get_reports():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasReport")


def rdf_get_regulatory_body():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasRegulatoryBody")


def rdf_get_propmod():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasPropMod")


def rdf_get_entity():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasEntity")


def rdf_get_frequency():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasReport")


def rdf_get_details():
    return ro_provider.get_all_from_type("http://dgfisma.com/reporting_obligation#hasDetails")