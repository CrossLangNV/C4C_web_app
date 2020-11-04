from SPARQLWrapper import SPARQLWrapper, JSON
import json
import logging as logger
import os

from obligations.models import ReportingObligation
from obligations import build_rdf
from obligations.build_rdf import D_ENTITIES, ExampleCasContent, ROGraph
from obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper, SPARQLGraphWrapper
from obligations.rdf_mock import rdf_get_reporters_mock, rdf_get_verbs_mock, rdf_get_reports_mock,\
    rdf_get_regulatory_body_mock, rdf_get_propmod_mock, rdf_get_entity_mock, rdf_get_frequency_mock

# You might have to change this
URL_FUSEKI = os.environ['RDF_FUSEKI_URL']


def rdf_get_entities():
    pass


def rdf_get_reporters():
    return rdf_get_reporters_mock()


def rdf_get_verbs():
    return rdf_get_verbs_mock()


def rdf_get_reports():
    return rdf_get_reports_mock()


def rdf_get_regulatory_body():
    return rdf_get_regulatory_body_mock()


def rdf_get_propmod():
    return rdf_get_propmod_mock()


def rdf_get_entity():
    return rdf_get_entity_mock()


def rdf_get_frequency():
    return rdf_get_frequency_mock()