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
GRAPH = 'graph'


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
            {cp_uri.n3()} rdf:type <http://www.w3.org/ns/dcat#ContactPoint> ;
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
    # PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
	# PREFIX cpsv: <http://purl.org/vocab/cpsv#>
	# PREFIX terms: <http://purl.org/dc/terms/>

    SELECT distinct ?{GRAPH}
    WHERE {{  
        Graph ?{GRAPH} {{ }}
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

    return l
