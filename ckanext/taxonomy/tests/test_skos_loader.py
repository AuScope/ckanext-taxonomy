"""Tests for the vendored SKOS concept loader.

These tests are self-contained (no CKAN dependency) and validate the
rdflib-based SKOS loader that replaced the abandoned python-skos package.
"""
import pytest
from rdflib import Graph, Literal, Namespace, URIRef, RDF

from ckanext.taxonomy.skos_loader import Concept, load_concepts, _pick_literal

SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
EX = Namespace("http://example.org/")


def _make_graph_with_concepts():
    """Build a small RDF graph with SKOS concepts for testing."""
    g = Graph()
    parent_uri = EX.parent
    child_uri = EX.child

    g.add((parent_uri, RDF.type, SKOS.Concept))
    g.add((parent_uri, SKOS.prefLabel, Literal("Parent", lang="en")))
    g.add((parent_uri, SKOS.prefLabel, Literal("Padre", lang="es")))
    g.add((parent_uri, SKOS.definition, Literal("A parent concept", lang="en")))

    g.add((child_uri, RDF.type, SKOS.Concept))
    g.add((child_uri, SKOS.prefLabel, Literal("Child", lang="en")))
    g.add((child_uri, SKOS.broader, parent_uri))

    return g


class TestLoadConcepts:

    def test_loads_concepts_from_graph(self):
        g = _make_graph_with_concepts()
        concepts = load_concepts(g, lang='en')
        assert len(concepts) == 2
        assert str(EX.parent) in concepts
        assert str(EX.child) in concepts

    def test_concept_labels(self):
        g = _make_graph_with_concepts()
        concepts = load_concepts(g, lang='en')
        assert concepts[str(EX.parent)].prefLabel == "Parent"
        assert concepts[str(EX.child)].prefLabel == "Child"

    def test_concept_definition(self):
        g = _make_graph_with_concepts()
        concepts = load_concepts(g, lang='en')
        assert concepts[str(EX.parent)].definition == "A parent concept"

    def test_language_selection(self):
        g = _make_graph_with_concepts()
        concepts = load_concepts(g, lang='es')
        assert concepts[str(EX.parent)].prefLabel == "Padre"

    def test_broader_narrower_relationships(self):
        g = _make_graph_with_concepts()
        concepts = load_concepts(g, lang='en')
        parent = concepts[str(EX.parent)]
        child = concepts[str(EX.child)]

        assert str(EX.child) in parent.narrower
        assert str(EX.parent) in child.broader
        assert not parent.broader

    def test_skos_narrower_triples(self):
        g = Graph()
        g.add((EX.a, RDF.type, SKOS.Concept))
        g.add((EX.a, SKOS.prefLabel, Literal("A", lang="en")))
        g.add((EX.b, RDF.type, SKOS.Concept))
        g.add((EX.b, SKOS.prefLabel, Literal("B", lang="en")))
        g.add((EX.a, SKOS.narrower, EX.b))

        concepts = load_concepts(g, lang='en')
        assert str(EX.b) in concepts[str(EX.a)].narrower
        assert str(EX.a) in concepts[str(EX.b)].broader

    def test_empty_graph(self):
        g = Graph()
        concepts = load_concepts(g)
        assert concepts == {}


class TestPickLiteral:

    def test_returns_matching_language(self):
        g = Graph()
        g.add((EX.x, SKOS.prefLabel, Literal("English", lang="en")))
        g.add((EX.x, SKOS.prefLabel, Literal("French", lang="fr")))
        assert _pick_literal(g, EX.x, SKOS.prefLabel, "fr") == "French"

    def test_falls_back_to_any(self):
        g = Graph()
        g.add((EX.x, SKOS.prefLabel, Literal("NoLang")))
        assert _pick_literal(g, EX.x, SKOS.prefLabel, "en") == "NoLang"

    def test_returns_empty_when_missing(self):
        g = Graph()
        assert _pick_literal(g, EX.x, SKOS.prefLabel, "en") == ""


class TestConcept:

    def test_defaults(self):
        c = Concept("http://example.org/test")
        assert c.uri == "http://example.org/test"
        assert c.prefLabel == ''
        assert c.definition == ''
        assert c.broader == {}
        assert c.narrower == {}
