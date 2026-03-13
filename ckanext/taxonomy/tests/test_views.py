"""Tests for the Flask blueprint and view wiring.

These tests validate the blueprint structure without requiring a full CKAN
environment. Tests that exercise the actual rendered pages need a running
CKAN app and should be validated in Docker/integration testing.
"""
import os
import pytest


_PLUGIN_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, 'plugin.py')


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

    def test_blueprint_has_taxonomy_detail_rule(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/<taxonomy_name>' in endpoints
        assert endpoints['/taxonomies/<taxonomy_name>']['endpoint'] == 'taxonomy_detail'

    def test_blueprint_has_term_detail_rule(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/term/<term_id>' in endpoints
        assert endpoints['/taxonomies/term/<term_id>']['endpoint'] == 'term_detail'

    def test_index_view_function_exists(self):
        from ckanext.taxonomy.views import index
        assert callable(index)

    def test_taxonomy_detail_view_function_exists(self):
        from ckanext.taxonomy.views import taxonomy_detail
        assert callable(taxonomy_detail)

    def test_term_detail_view_function_exists(self):
        from ckanext.taxonomy.views import term_detail
        assert callable(term_detail)


class TestAdminRoutes:
    """Verify that admin CRUD routes are registered with correct methods."""

    def test_taxonomy_create_route(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/new' in endpoints
        ep = endpoints['/taxonomies/new']
        assert ep['endpoint'] == 'taxonomy_create'
        assert 'GET' in ep['methods']
        assert 'POST' in ep['methods']

    def test_taxonomy_edit_route(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/<taxonomy_name>/edit' in endpoints
        ep = endpoints['/taxonomies/<taxonomy_name>/edit']
        assert ep['endpoint'] == 'taxonomy_edit'
        assert 'GET' in ep['methods']
        assert 'POST' in ep['methods']

    def test_taxonomy_delete_route(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/<taxonomy_name>/delete' in endpoints
        ep = endpoints['/taxonomies/<taxonomy_name>/delete']
        assert ep['endpoint'] == 'taxonomy_delete'
        assert 'POST' in ep['methods']

    def test_term_create_route(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/<taxonomy_name>/term/new' in endpoints
        ep = endpoints['/taxonomies/<taxonomy_name>/term/new']
        assert ep['endpoint'] == 'term_create'
        assert 'GET' in ep['methods']
        assert 'POST' in ep['methods']

    def test_term_edit_route(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/term/<term_id>/edit' in endpoints
        ep = endpoints['/taxonomies/term/<term_id>/edit']
        assert ep['endpoint'] == 'term_edit'
        assert 'POST' in ep['methods']

    def test_term_delete_route(self):
        from ckanext.taxonomy.views import taxonomy_blueprint
        endpoints = _get_blueprint_endpoints(taxonomy_blueprint)
        assert '/taxonomies/term/<term_id>/delete' in endpoints
        ep = endpoints['/taxonomies/term/<term_id>/delete']
        assert ep['endpoint'] == 'term_delete'
        assert 'POST' in ep['methods']

    def test_admin_crud_view_functions_callable(self):
        from ckanext.taxonomy import views
        for fn_name in ['taxonomy_create', 'taxonomy_edit',
                        'taxonomy_delete_view', 'term_create',
                        'term_edit', 'term_delete_view']:
            assert callable(getattr(views, fn_name)), \
                f"{fn_name} should be callable"

    def test_count_descendants_helper(self):
        from ckanext.taxonomy.views import _count_descendants
        terms = [
            {'id': '1', 'parent_id': None},
            {'id': '2', 'parent_id': '1'},
            {'id': '3', 'parent_id': '1'},
            {'id': '4', 'parent_id': '2'},
        ]
        assert _count_descendants('1', terms) == 3
        assert _count_descendants('2', terms) == 1
        assert _count_descendants('3', terms) == 0


class TestPluginIntegration:

    def test_plugin_declares_iblueprint(self):
        source = open(_PLUGIN_PATH).read()
        assert 'IBlueprint' in source
        assert 'get_blueprint' in source

    def test_plugin_no_iroutes_reference(self):
        source = open(_PLUGIN_PATH).read()
        assert 'IRoutes' not in source


class TestTemplateFiles:
    """Verify that all expected template files exist."""

    _TEMPLATE_DIR = os.path.join(
        os.path.dirname(__file__), os.pardir,
        'templates', 'ckanext', 'taxonomy')

    @pytest.mark.parametrize('filename', [
        'index.html',
        'taxonomy_detail.html',
        'term_detail.html',
        'taxonomy_form.html',
        'term_form.html',
        'confirm_delete.html',
    ])
    def test_template_exists(self, filename):
        path = os.path.join(self._TEMPLATE_DIR, filename)
        assert os.path.isfile(path), f"Template {filename} missing"

    def test_header_override_exists(self):
        header = os.path.join(
            os.path.dirname(__file__), os.pardir,
            'templates', 'header.html')
        assert os.path.isfile(header), "header.html override missing"

    def test_header_contains_taxonomy_nav(self):
        header = os.path.join(
            os.path.dirname(__file__), os.pardir,
            'templates', 'header.html')
        source = open(header).read()
        assert 'taxonomy.index' in source
        assert 'Taxonomies' in source


class TestStaticAssets:
    """Verify CSS and JS files exist."""

    _PUBLIC_DIR = os.path.join(
        os.path.dirname(__file__), os.pardir, 'public')

    def test_admin_css_exists(self):
        path = os.path.join(self._PUBLIC_DIR, 'css', 'taxonomy-admin.css')
        assert os.path.isfile(path)

    def test_admin_js_exists(self):
        path = os.path.join(self._PUBLIC_DIR, 'scripts', 'taxonomy-admin.js')
        assert os.path.isfile(path)
