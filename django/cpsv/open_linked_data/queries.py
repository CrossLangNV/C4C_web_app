from typing import List

from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib.namespace import DCAT, Namespace, SKOS
from rdflib.term import Literal, URIRef

from cpsv.open_linked_data.build_rdf import CPSV

TYPE_CONTACT_POINT = DCAT.ContactPoint

TYPE_PUBLICSERVICE = Namespace('http://purl.org/vocab/cpsv#').PublicService

URI = "uri"
TITLE = "title"
DESCRIPTION = 'description'
PRED = "pred"
LABEL = 'label'
GRAPH = 'graph'

PS = 'publicService'


def get_types(endpoint):
    OBJECT = "object"

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT distinct ?{OBJECT}
    WHERE {{  Graph ?{GRAPH} {{
        ?subject rdf:type ?{OBJECT}
        }}
    }}
    """

    l = [d.get(OBJECT) for d in shared_query_func(q, endpoint)]

    return l


def get_contact_points(endpoint, graph_uri=None):
    q_filter = f"""
    values ?{GRAPH} {{ {URIRef(graph_uri).n3()} }} 
    """ if graph_uri is not None else ''

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

    SELECT distinct ?{URI} ?{GRAPH}
    WHERE {{ 
        {q_filter} 
        Graph ?{GRAPH} {{
            ?{URI} rdf:type {TYPE_CONTACT_POINT.n3()} ;
        }}
    }}
    """

    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_contact_point_info(endpoint, cp_uri,
                           graph_uri=None):
    if not isinstance(cp_uri, URIRef):
        cp_uri = URIRef(cp_uri)

    q_filter = f"""
    values ?{GRAPH} {{ {URIRef(graph_uri).n3()} }} 
    """ if graph_uri is not None else ''

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX schema: <https://schema.org/>
    PREFIX vcard2006: <http://www.w3.org/2006/vcard/ns#>

    SELECT distinct ({cp_uri.n3()} as ?{URI}) ?{PRED} ?{LABEL} ?{GRAPH}
    WHERE {{  
        {q_filter} 
        Graph ?{GRAPH} {{
            VALUES ?{PRED} {{schema:openingHours vcard2006:hasTelephone vcard2006:hasEmail}} 
            {cp_uri.n3()} rdf:type {DCAT.ContactPoint.n3()} ;
                ?{PRED} ?{LABEL} .     
        }}    
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_public_services(endpoint, graph_uri=None):
    q_filter = f"""
    values ?{GRAPH} {{ {URIRef(graph_uri).n3()} }} 
    """ if graph_uri is not None else ''

    q = f"""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	PREFIX cpsv: <http://purl.org/vocab/cpsv#>
	PREFIX terms: <http://purl.org/dc/terms/>

    SELECT distinct ?{URI} ?{TITLE} ?{DESCRIPTION} ?{GRAPH}
    WHERE {{ 
        {q_filter}
        Graph ?{GRAPH} {{
            ?{URI} rdf:type {TYPE_PUBLICSERVICE.n3()} ;
                terms:title ?{TITLE} ;
                terms:description ?{DESCRIPTION} . 
        }}
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_graphs(endpoint):
    q = f"""
    SELECT distinct ?{GRAPH}
    WHERE {{  
        Graph ?{GRAPH} {{ }}
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_concepts(endpoint,
                 graph_uri=None,
                 ):
    """ Return all concepts

    :param endpoint:
    :param graph_uri: (Optional). To filter based on municipality

    :return:
    """

    q_filter = f"""
    values ?{GRAPH} {{ {URIRef(graph_uri).n3()} }}
    """ if graph_uri is not None else ''

    q = f"""
    PREFIX skos: {URIRef(str(SKOS)).n3()}

    SELECT distinct ?{LABEL}
    WHERE {{
        {q_filter}
        Graph ?{GRAPH} {{ 
            ?concept skos:prefLabel ?{LABEL}
        }}
    }}
    """
    # print(q)

    l = shared_query_func(q, endpoint)

    return l


def get_classified_by_concepts(endpoint,
                               public_service: URIRef = None,
                               graph_uri=None,
                               ) -> List[dict]:
    """ Not only return the concepts, but also the public services they are linked with.

    :param endpoint:
    :param public_service:
    :param graph_uri:
    :return:
    """

    q_filter = f"""
    values ?{GRAPH} {{ {URIRef(graph_uri).n3()} }}
    """ if graph_uri is not None else ''

    q_filter_ps = f"""
    values ?{PS} {{ {URIRef(public_service).n3()} }}
    """ if public_service is not None else ''

    q = f"""
    PREFIX skos: {URIRef(str(SKOS)).n3()}
    PREFIX cpsv: {URIRef(CPSV).n3()}

    SELECT distinct ?{LABEL} ?{PS}
    WHERE {{
        {q_filter}
        {q_filter_ps}
        Graph ?{GRAPH} {{ 
            ?{PS} cpsv:isClassifiedBy ?concept .
            ?concept skos:prefLabel ?{LABEL}
        }}
    }}
    """

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

    return l