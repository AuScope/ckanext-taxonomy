"""
Minimal SKOS concept loader using rdflib.

Replaces the abandoned python-skos library. Only implements the subset
of functionality used by the taxonomy load command: parsing an RDF graph
for SKOS concepts and returning them with labels, URIs, and hierarchy.
"""
from rdflib import Namespace, RDF

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


class Concept:
    __slots__ = ('uri', 'prefLabel', 'definition', 'broader', 'narrower')

    def __init__(self, uri):
        self.uri = str(uri)
        self.prefLabel = ''
        self.definition = ''
        self.broader = {}
        self.narrower = {}


def load_concepts(graph, lang='en'):
    """Load SKOS concepts from an rdflib Graph.

    Returns a dict mapping URI (str) -> Concept, with broader/narrower
    relationships resolved.
    """
    concepts = {}

    for subject in graph.subjects(RDF.type, SKOS.Concept):
        uri = str(subject)
        concept = concepts.setdefault(uri, Concept(uri))

        concept.prefLabel = _pick_literal(graph, subject, SKOS.prefLabel, lang)
        concept.definition = _pick_literal(graph, subject, SKOS.definition, lang)

    for subject, _, obj in graph.triples((None, SKOS.broader, None)):
        child_uri = str(subject)
        parent_uri = str(obj)
        child = concepts.get(child_uri)
        parent = concepts.get(parent_uri)
        if child and parent:
            child.broader[parent_uri] = parent
            parent.narrower[child_uri] = child

    for subject, _, obj in graph.triples((None, SKOS.narrower, None)):
        parent_uri = str(subject)
        child_uri = str(obj)
        parent = concepts.get(parent_uri)
        child = concepts.get(child_uri)
        if parent and child:
            if child_uri not in parent.narrower:
                parent.narrower[child_uri] = child
            if parent_uri not in child.broader:
                child.broader[parent_uri] = parent

    return concepts


def _pick_literal(graph, subject, predicate, lang):
    """Return the best matching literal for the given language."""
    best = ''
    for _, _, obj in graph.triples((subject, predicate, None)):
        val = str(obj)
        if getattr(obj, 'language', None) == lang:
            return val
        if not best:
            best = val
    return best
