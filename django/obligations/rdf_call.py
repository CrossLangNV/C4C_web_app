from SPARQLWrapper import SPARQLWrapper, JSON
import json
import logging as logger
import os
from typing import List, Tuple


from obligations.models import ReportingObligation
from obligations import build_rdf
from obligations.build_rdf import D_ENTITIES, ExampleCasContent, ROGraph
from obligations.rdf_parser import SPARQLReportingObligationProvider, RDFLibGraphWrapper, SPARQLGraphWrapper

# You might have to change this
URL_FUSEKI = os.environ['RDF_FUSEKI_URL']
graph_wrapper = SPARQLGraphWrapper(URL_FUSEKI)
ro_provider = SPARQLReportingObligationProvider(graph_wrapper)


def rdf_get_name_of_entity(entity):
    entity_dict = {
            "http://dgfisma.com/reporting_obligations/hasEntity": "Entity",
            "http://dgfisma.com/reporting_obligations/hasPropExt": "Extent",
            "http://dgfisma.com/reporting_obligations/hasReporter": "Reporter",
            "http://dgfisma.com/reporting_obligations/hasRegulatoryBody": "Regulatory Body",
            "http://dgfisma.com/reporting_obligations/hasPropCau": "Cause",
            "http://dgfisma.com/reporting_obligations/hasPropMod": "Modal",
            "http://dgfisma.com/reporting_obligations/hasPropPnc": "Purpose Not Cause",
            "http://dgfisma.com/reporting_obligations/hasVerb": "Verb",
            "http://dgfisma.com/reporting_obligations/hasDetails": "Details",
            "http://dgfisma.com/reporting_obligations/hasPropDir": "Directional",
            "http://dgfisma.com/reporting_obligations/hasPropLoc": "Locative",
            "http://dgfisma.com/reporting_obligations/hasPropAdv": "Adverbials",
            "http://dgfisma.com/reporting_obligations/hasPropNeg": "Negation",
            "http://dgfisma.com/reporting_obligations/hasPropDis": "Discourse",
            "http://dgfisma.com/reporting_obligations/hasReport": "Report",
            "http://dgfisma.com/reporting_obligations/hasPropMnr": "Manner",
            "http://dgfisma.com/reporting_obligations/hasPropTmp": "Temporal",
            "http://dgfisma.com/reporting_obligations/hasPropCom": "Comitative",
            "http://dgfisma.com/reporting_obligations/hasPropGol": "Goal",
            "http://dgfisma.com/reporting_obligations/hasPropLVB": "Light Verb",
            "http://dgfisma.com/reporting_obligations/hasPropDsp": "Direct Speech",
            "http://dgfisma.com/reporting_obligations/hasPropRec": "Reciprocals",
            "http://dgfisma.com/reporting_obligations/hasPropPrd": "Secondary Predication",
            "http://dgfisma.com/reporting_obligations/hasPropPrp": "Purpose"
    }
    return entity_dict[entity]


def rdf_get_available_entities():
    entities_list = ro_provider.get_different_entities()
    return entities_list


def rdf_get_predicate(predicate):
    return ro_provider.get_all_from_type(predicate)


# Test this in the console
def rdf_get_all_reporting_obligations():
    return ro_provider.get_all_ro_str()


# Single query
def rdf_query_predicate_single(predicate, query):
    return ro_provider.get_filter_single(f"http://dgfisma.com/reporting_obligations/{predicate}", query)


# Example: rdf_query_predicate([("http://dgfisma.com/reporting_obligation#hasReporter", "by the ECB")])
def rdf_query_predicate_multiple(list_pred_value: List[Tuple[str]]):
    return ro_provider.get_filter_multiple(list_pred_value)


def rdf_query_predicate_multiple_id(list_pred_value: List[Tuple[str]]):
    return ro_provider.get_filter_ro_id_multiple(list_pred_value)

