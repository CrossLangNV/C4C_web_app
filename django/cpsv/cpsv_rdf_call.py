from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Literal, URIRef
from rdflib.namespace import DCAT, Namespace

TYPE_CONTACT_POINT = DCAT.ContactPoint

TYPE_PUBLICSERVICE = Namespace('http://purl.org/vocab/cpsv#').PublicService

URI = "uri"
TITLE = "title"
DESCRIPTION = 'description'
PRED = "pred"
LABEL = 'label'


def get_types(endpoint):
    OBJECT = "object"

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT distinct ?{OBJECT}
    WHERE {{
        ?subject rdf:type ?{OBJECT}
    }}
    """

    l = [d.get(OBJECT) for d in shared_query_func(q, endpoint)]

    return l


def get_contact_points(endpoint):
    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT distinct ?{URI}
    WHERE {{
        ?{URI} rdf:type {TYPE_CONTACT_POINT.n3()} ;
    }}
    """

    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_contact_point_info(endpoint, cp_uri):
    if not isinstance(cp_uri, URIRef):
        cp_uri = URIRef(cp_uri)

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX schema: <https://schema.org/>
    PREFIX vcard2006: <http://www.w3.org/2006/vcard/ns#>

    SELECT distinct ({cp_uri.n3()} as ?{URI}) ?{PRED} ?{LABEL}
    WHERE {{
        VALUES ?{PRED} {{schema:openingHours vcard2006:hasTelephone vcard2006:hasEmail}} 
        {cp_uri.n3()} rdf:type <http://www.w3.org/ns/dcat#ContactPoint> ;
            ?{PRED} ?{LABEL} .         
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_public_services(endpoint):
    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX cpsv: <http://purl.org/vocab/cpsv#>
	PREFIX terms: <http://purl.org/dc/terms/>

    SELECT distinct ?{URI} ?{TITLE} ?{DESCRIPTION}
    WHERE {{
        ?{URI} rdf:type {TYPE_PUBLICSERVICE.n3()} ;
        	terms:title ?{TITLE} ;
            terms:description ?{DESCRIPTION} . 
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def shared_query_func(q, endpoint):
    sparql = SPARQLWrapper(endpoint)

    "RDF"
    sparql.setReturnFormat(JSON)  # JSON

    sparql.setQuery(q)

    results = sparql.query().convert()

    l = []
    for result in results["results"]["bindings"]:
        l.append(
            {k: (URIRef(v['value']) if v.get('type') == 'uri' else Literal(v['value']))
             for k, v in result.items()
             })

    # l = [
    #     tuple(result[k]["value"] for k in tuple_keys) for result in results["results"]["bindings"]
    #     #     result[OBJECT]["value"] for result in results["results"]["bindings"]
    # ]

    return l