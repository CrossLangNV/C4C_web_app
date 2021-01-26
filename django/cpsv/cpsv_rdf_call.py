from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib.namespace import DCAT, Namespace, URIRef

TYPE_CONTACT_POINT = DCAT.ContactPoint

TYPE_PUBLICSERVICE = Namespace('http://purl.org/vocab/cpsv#').PublicService


def get_types(endpoint):
    OBJECT = "object"

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT distinct ?{OBJECT}
    WHERE {{
        ?subject rdf:type ?{OBJECT}
    }}
    """

    l = [e0 for e0, *_ in shared_query_func(q, endpoint, tuple_keys=(OBJECT, ))]

    return l


def get_contact_points(endpoint):
    URI = "uri"

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT distinct ?{URI}
    WHERE {{
        ?{URI} rdf:type {TYPE_CONTACT_POINT.n3()} ;
    }}
    """

    print(q)

    l = shared_query_func(q, endpoint, tuple_keys=(URI, ))

    return l


def get_contact_point_info(endpoint, cp_uri):
    if not isinstance(cp_uri, URIRef):
        cp_uri = URIRef(cp_uri)

    # todo


def get_public_services(endpoint):
    URL = "uri"
    TITLE = "title"
    DESCRIPTION = 'discr'

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX cpsv: <http://purl.org/vocab/cpsv#>
	PREFIX terms: <http://purl.org/dc/terms/>

    SELECT distinct ?{URL} ?{TITLE} ?{DESCRIPTION}
    WHERE {{
        ?{URL} rdf:type {TYPE_PUBLICSERVICE.n3()} ;
        	terms:title ?{TITLE} ;
            terms:description ?{DESCRIPTION} . 
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint, tuple_keys=(URL, TITLE, DESCRIPTION))

    return l


def shared_query_func(q, endpoint, tuple_keys):
    sparql = SPARQLWrapper(endpoint)

    sparql.setReturnFormat(JSON)

    sparql.setQuery(q)

    results = sparql.query().convert()

    l = [
        tuple(result[k]["value"] for k in tuple_keys) for result in results["results"]["bindings"]
        #     result[OBJECT]["value"] for result in results["results"]["bindings"]
    ]

    return l