import os

from cpsv.rdf_parser import *

SPARQL_ENDPOINT = os.environ["RDF_FUSEKI_URL"]
provider = SPARQLPublicServicesProvider(SPARQL_ENDPOINT)


def get_dropdown_options(uri):
    if uri == "http://www.w3.org/ns/dcat#hasContactPoint":
        result = get_contact_points()
        for d in result:
            d['label'] = d.get('uri')

    elif uri == "http://data.europa.eu/m8g/hasCompetentAuthority":
        result = get_competent_authorities()
    elif uri == "http://purl.org/vocab/cpsv#isClassifiedBy":
        result = get_related_concepts()



    return result


def get_public_services():
    return provider.get_public_service_uris()


def get_contact_points(*args, **kwargs):
    return provider.get_contact_points(*args, **kwargs)


def get_competent_authorities(*args, **kwargs):
    return provider.get_competent_authorities(*args, **kwargs)


def get_related_concepts(*args, **kwargs):
    return provider.get_concepts(*args, **kwargs)


def get_relations():
    return provider.get_relations()
