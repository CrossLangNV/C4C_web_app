from rdflib.graph import Graph
from rdflib.namespace import RDF, Namespace, DCAT, DCTERMS, SKOS
from rdflib.term import Literal, URIRef
from rdflib.term import _serial_number_generator

from cpsv.open_linked_data.node import PublicService, ContactPoint, PublicOrganization

CPSV = Namespace("http://purl.org/vocab/cpsv#")
CV = Namespace("http://data.europa.eu/m8g/")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

C4C = Namespace("http://cefat4cities.crosslang.com/content/")
SCHEMA = Namespace("https://schema.org/")


class CPSV_APGraph(Graph):

    def __init__(self, *args, **kwargs):
        super(CPSV_APGraph, self).__init__(*args, **kwargs)

        self.bind("rdf", RDF)
        self.bind('cpsv', CPSV)
        self.bind('dct', DCTERMS)
        self.bind('dcat', DCAT)
        self.bind('vcard', VCARD)
        self.bind('schema', SCHEMA)
        self.bind('skos', SKOS)
        self.bind('c4c', C4C)

    def add_contact_point(self, contact_point: ContactPoint):
        """ Add new contact points to the RDF as CPSV-AP Contact Points.

        :param contact_point: a contact point object
        :return:
            If contact info was found, it returns URI to contact_info
        """

        l_emails = contact_point.get_l_emails()
        l_opening_hours = contact_point.get_l_opening_hours()
        l_phone = contact_point.get_l_phone()

        if not (len(l_emails) or len(l_opening_hours) or len(l_phone)):
            # No contact info found
            return

        val = 'contactPoint' + id_generator()
        uri_ref = URIRef(val, base=C4C)

        self.add((uri_ref, RDF.type, RDF.Description))
        self.add((uri_ref, RDF.type, DCAT.ContactPoint))  # ['ContactPoPublicService']))

        for email in l_emails:
            self.add((uri_ref,
                      VCARD.hasEmail,
                      Literal(email)))

        for opening_hour in l_opening_hours:
            # TODO fine-tune
            self.add((uri_ref,
                      SCHEMA.openingHours,
                      Literal(opening_hour)))

        for phone in l_phone:
            self.add((uri_ref,
                      VCARD.hasTelephone,
                      Literal(phone)))

        return uri_ref

    def add_public_service(self, public_service: PublicService):
        uri = public_service.uri
        uri_ref = URIRef(uri)

        title = public_service.title

        self.add((uri_ref, RDF.type, RDF.Description))
        self.add((uri_ref, RDF.type, CPSV.PublicService))

        # Mandatory
        self.add((uri_ref, DCTERMS.identifier, Literal(title_to_identifier(title))))
        self.add((uri_ref, DCTERMS.description, Literal('TODO')))  # TODO
        self.add((uri_ref, DCTERMS.title, Literal(title)))

        return uri_ref

    def add_public_organization(self, public_organization: PublicOrganization):
        """
        If it already exists, nothing is changed

        :param public_organization:
        :return:
        """

        label = public_organization.get_preferred_label()
        loc_uri = URIRef(public_organization.get_spatial())

        q = """

        """

        t_label = [None, SKOS.prefLabel, Literal(title_to_identifier(label))]
        t_spatial = [None, DCTERMS.spatial, loc_uri]

        def get_uri():
            """ Private helper function. Return

            :return: The URI for the public organisation.
            """
            # TODO needs refactoring. Although it works, it's prone to fail if changes are made to the code

            t_existing0 = self.triples(t_label)
            t_existing1 = self.triples(t_spatial)

            for s0, _, _ in t_existing0:
                for s1, _, _ in t_existing1:
                    if s0 == s1:
                        print(s0)
                        return s0

            # Nothing found
            val = 'publicOrganization' + id_generator()
            uri_ref = URIRef(val, base=C4C)
            return uri_ref

        uri_ref = get_uri()

        t_label[0] = uri_ref
        t_spatial[0] = uri_ref

        self.add((uri_ref, RDF.type, RDF.Description))
        self.add((uri_ref, RDF.type, CV.PublicOrganisation))

        # Mandatory
        self.add(t_label)
        self.add(t_spatial)

        return uri_ref

    def link_ps_cp(self, ps_uri, cp_uri):

        if not isinstance(ps_uri, URIRef):
            # EAFP
            ps_uri = URIRef(ps_uri)

        if not isinstance(cp_uri, URIRef):
            # EAFP
            cp_uri = URIRef(cp_uri)

        self.add((URIRef(ps_uri), DCAT.hasContactPoint, URIRef(cp_uri)))

    def link_ps_po(self, ps_uri, po_uri):
        """

        :param ps_uri: URI to Public Service
        :param po_uri: URI to Public Organization
        :return:
        """

        self.add((URIRef(ps_uri), CV.hasCompetentAuthority, URIRef(po_uri)))

    def add_concepts(self, l_terms, public_service_uri: URIRef):

        if not isinstance(public_service_uri, URIRef):
            # EAFP
            public_service_uri = URIRef(public_service_uri)

        q = """
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

        SELECT ?subject
        WHERE {{
            ?subject rdf:type skos:Concept ;
                skos:prefLabel "{term}" .  
        }}
        """

        l_uri = []

        for term in l_terms:

            r = [s for s, *_ in self.query(q.format(term=term))]

            if len(r):
                l_uri.extend(r)

            # Add to graph if it doesn't exist yet
            else:
                val = 'concept' + id_generator()
                uri_ref = URIRef(val, base=C4C)

                self.add((uri_ref, RDF.type, RDF.Description))
                self.add((uri_ref, RDF.type, SKOS.Concept))  # ['ContactPoPublicService']))
                self.add((uri_ref, SKOS.prefLabel, Literal(term)))

                l_uri.append(uri_ref)

        # Link to public service
        for uri in l_uri:
            self.add((public_service_uri, CPSV.isClassifiedBy, uri))

        return

    def add_life_events(self, l_life_events, public_service_uri: URIRef):
        """ Add life events to the graph

        :param l_life_events:
        :param public_service_uri:
        :return:
        """

        if not isinstance(public_service_uri, URIRef):
            # EAFP
            public_service_uri = URIRef(public_service_uri)

        l_uri = []

        for title in l_life_events:

            # Cast to _literal_n3 to make sure special characters are handled correctly.
            q = f"""

            PREFIX dct: <http://purl.org/dc/terms/>
            PREFIX cpsv: <{CPSV}>

            SELECT ?subject
            WHERE {{
                ?subject rdf:type cpsv:LifeEvent ;
                    dct:title {Literal(title)._literal_n3()} .
            }}
            """

            r = [s for s, *_ in self.query(q)]

            if len(r):
                l_uri.extend(r)

            # Add to graph if it doesn't exist yet
            else:
                val = 'lifeEvent' + id_generator()
                uri_ref = URIRef(val, base=C4C)

                self.add((uri_ref, RDF.type, RDF.Description))
                self.add((uri_ref, RDF.type, CPSV.LifeEvent))

                # Mandatory
                self.add((uri_ref, DCTERMS.identifier, Literal(title_to_identifier(title))))  # TODO
                self.add((uri_ref, DCTERMS.title, Literal(title)))

                l_uri.append(uri_ref)

        # # Link to public service
        for uri in l_uri:
            self.add((public_service_uri, CPSV.isClassifiedBy, uri))
            self.add((uri, CPSV.isGroupedBy, public_service_uri))

        return


def title_to_identifier(s: str):
    return s.title().replace(' ', '')


def id_generator():
    # def id_generator(size=12, chars=string.ascii_lowercase + string.digits):
    #     return ''.join(random.choice(chars) for _ in range(size))
    return _serial_number_generator()()