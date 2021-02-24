import os

from cpsv.rdf_parser import *

SPARQL_ENDPOINT = os.environ["RDF_FUSEKI_URL"]
provider_public_service = SPARQLPublicServicesProvider(SPARQL_ENDPOINT)
provider_contact_point = SPARQLContactPointProvider(SPARQL_ENDPOINT)


def get_dropdown_options_for_public_services(uri):
    if uri == "http://www.w3.org/ns/dcat#hasContactPoint":
        result = get_contact_points()
    elif uri == "http://data.europa.eu/m8g/hasCompetentAuthority":
        result = get_competent_authorities()
    elif uri == "http://purl.org/vocab/cpsv#isClassifiedBy":
        result = get_related_concepts()
    else:
        result = []

    for d in result:
        if not d.get(LABEL):
            d[LABEL] = d.get(URI)

    return result


def get_dropdown_options_for_contact_points(uri):
    if uri == "http://www.w3.org/ns/dcat#hasContactPoint":
        result = get_public_services_from_contact_points()
    else:
        result = []

    for d in result:
        if not d.get(LABEL):
            d[LABEL] = d.get(URI)

    return result


def get_public_services():
    return provider_public_service.get_public_service_uris()


def get_contact_points(*args, **kwargs):
    return provider_public_service.get_contact_points(*args, **kwargs)


def get_competent_authorities(*args, **kwargs):
    return provider_public_service.get_competent_authorities(*args, **kwargs)


def get_related_concepts(*args, **kwargs):
    return provider_public_service.get_concepts(*args, **kwargs)


def get_relations():
    return provider_public_service.get_relations()


def get_public_service_uris_filter(*args, **kwargs):
    return provider_public_service.get_public_service_uris_filter(*args, **kwargs)


# For contact points UI

def get_public_services_from_contact_points(*args, **kwargs):
    return provider_contact_point.get_public_services(*args, **kwargs)


def get_contact_point_uris_filter(*args, **kwargs):
    return provider_contact_point.get_contact_point_uris_filter(*args, **kwargs)