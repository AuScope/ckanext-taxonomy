"""Tests for the Flask blueprint and view wiring.

These tests validate the blueprint structure without requiring a full CKAN
environment. Tests that exercise the actual rendered pages need a running
CKAN app and should be validated in Docker/integration testing.
"""
import os
import pytest


_PLUGIN_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, 'plugin.py')


class TestTaxonomyBlueprint:

    def test_blueprint_exists(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        assert taxonomy_blueprint is not None
        assert taxonomy_blueprint.name == 'taxonomy'

    def test_blueprint_has_index_rule(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies' in endpoints
        assert endpoints['/taxonomies']['endpoint'] == 'index'

    def test_blueprint_has_show_rule(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/<name>' in endpoints
        assert endpoints['/taxonomies/<name>']['endpoint'] == 'show'

    def test_index_view_function_exists(self):
        from ckanext.taxonomy.views import index
        assert callable(index)

    def test_show_view_function_exists(self):
        from ckanext.taxonomy.views import show
        assert callable(show)

    def test_plugin_declares_iblueprint(self):
        source = open(_PLUGIN_PATH).read()
        assert 'IBlueprint' in source
        assert 'get_blueprint' in source

    def test_plugin_no_iroutes_reference(self):
        source = open(_PLUGIN_PATH).read()
        assert 'IRoutes' not in source


def _get_blueprint_endpoints(bp):
    """Extract registered URL rules from a Flask Blueprint.

    Blueprints defer rule registration, so we replay them against a
    temporary Flask app to inspect the result.
    """
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(bp)
    endpoints = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith(bp.name + '.'):
            endpoints[rule.rule] = {
                'endpoint': rule.endpoint.split('.', 1)[1],
                'methods': rule.methods,
            }
    return endpoints
