from typing import Dict

from dgfisma_rdf.concepts.build_rdf import ConceptGraph as ConceptGraph_, EN
from rdflib import Literal, URIRef
from rdflib.namespace import SKOS, RDF


class ConceptGraph(ConceptGraph_):
    """
    There is a need to be able to add terms with predefined uri's
    """

    def add_terms_with_uri(self, d_terms: Dict[str, str], lang=EN):
        """ Add new terms to the RDF as SKOS concepts.

        Args:
            l_terms: List of the terms in string format
            lang: optional language parameter of the terms.

        Returns:
            list of RDF URI's of the new SKOS concepts.
        """

        l_uri = [None for _ in d_terms]  # Initialisation

        for i, (uri, term_i) in enumerate(d_terms.items()):
            node_term_i = URIRef(uri)

            l_uri[i] = node_term_i

            self.add((node_term_i,
                      RDF.type,
                      SKOS.Concept
                      ))

            self.add((node_term_i,
                      SKOS.prefLabel,
                      Literal(term_i, lang=lang)
                      ))

        return l_uri