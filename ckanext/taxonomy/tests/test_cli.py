"""Tests for Click CLI commands and YAML seed parsing.

- CLI structure tests validate command/option wiring via Click introspection
  (no CKAN env required).
- parse_yaml tests exercise the pure-Python YAML parser directly.
- Plugin integration tests verify IClick registration via source inspection.
"""
import os
import tempfile
import textwrap

import click
import pytest
import yaml

from ckanext.taxonomy.cli import taxonomy, get_commands
from ckanext.taxonomy.seed import parse_yaml

_PLUGIN_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, 'plugin.py')


# ── CLI structure ────────────────────────────────────────────────────

class TestCLIStructure:

    def test_taxonomy_is_click_group(self):
        assert isinstance(taxonomy, click.Group)

    def test_group_has_initdb_command(self):
        assert 'initdb' in taxonomy.commands

    def test_group_has_seed_defaults_command(self):
        assert 'seed-defaults' in taxonomy.commands

    def test_initdb_has_no_required_options(self):
        cmd = taxonomy.commands['initdb']
        required = [p for p in cmd.params if p.required]
        assert required == []

    def test_seed_defaults_has_file_option(self):
        cmd = taxonomy.commands['seed-defaults']
        names = {p.name for p in cmd.params}
        assert 'filepath' in names

    def test_seed_defaults_file_is_required(self):
        cmd = taxonomy.commands['seed-defaults']
        file_param = next(p for p in cmd.params if p.name == 'filepath')
        assert file_param.required is True

    def test_seed_defaults_has_force_flag(self):
        cmd = taxonomy.commands['seed-defaults']
        names = {p.name for p in cmd.params}
        assert 'force' in names

    def test_seed_defaults_has_sync_flag(self):
        cmd = taxonomy.commands['seed-defaults']
        names = {p.name for p in cmd.params}
        assert 'sync' in names

    def test_get_commands_returns_list_with_group(self):
        result = get_commands()
        assert isinstance(result, list)
        assert taxonomy in result


# ── parse_yaml ───────────────────────────────────────────────────────

class TestParseYAML:

    def _write_yaml(self, data):
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        yaml.safe_dump(data, f)
        f.close()
        return f.name

    def test_parse_valid_yaml(self):
        path = self._write_yaml({
            'taxonomies': [
                {'name': 'topics', 'title': 'Topics', 'terms': [
                    {'label': 'Science'},
                ]}
            ]
        })
        try:
            result = parse_yaml(path)
            assert len(result) == 1
            assert result[0]['name'] == 'topics'
        finally:
            os.unlink(path)

    def test_parse_multiple_taxonomies(self):
        path = self._write_yaml({
            'taxonomies': [
                {'name': 'a', 'title': 'A'},
                {'name': 'b', 'title': 'B'},
            ]
        })
        try:
            result = parse_yaml(path)
            assert len(result) == 2
        finally:
            os.unlink(path)

    def test_parse_nested_terms(self):
        path = self._write_yaml({
            'taxonomies': [{
                'name': 'geo',
                'terms': [
                    {'label': 'Europe', 'terms': [
                        {'label': 'France'},
                        {'label': 'Germany'},
                    ]},
                ],
            }]
        })
        try:
            result = parse_yaml(path)
            europe = result[0]['terms'][0]
            assert europe['label'] == 'Europe'
            assert len(europe['terms']) == 2
        finally:
            os.unlink(path)

    def test_parse_rejects_missing_taxonomies_key(self):
        path = self._write_yaml({'items': []})
        try:
            with pytest.raises(ValueError, match="must contain a 'taxonomies' key"):
                parse_yaml(path)
        finally:
            os.unlink(path)

    def test_parse_rejects_empty_file(self):
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False, encoding='utf-8')
        f.write('')
        f.close()
        try:
            with pytest.raises(ValueError, match="must contain a 'taxonomies' key"):
                parse_yaml(f.name)
        finally:
            os.unlink(f.name)

    def test_parse_preserves_extras(self):
        path = self._write_yaml({
            'taxonomies': [{
                'name': 'test',
                'terms': [
                    {'label': 'A', 'uri': 'http://example.com/a',
                     'extras': {'code': '01'}},
                ],
            }]
        })
        try:
            result = parse_yaml(path)
            term = result[0]['terms'][0]
            assert term['extras'] == {'code': '01'}
            assert term['uri'] == 'http://example.com/a'
        finally:
            os.unlink(path)


# ── Plugin integration ───────────────────────────────────────────────

class TestPluginCLIRegistration:

    def test_plugin_declares_iclick(self):
        source = open(_PLUGIN_PATH).read()
        assert 'IClick' in source
        assert 'get_commands' in source

    def test_plugin_imports_cli_module(self):
        source = open(_PLUGIN_PATH).read()
        assert 'ckanext.taxonomy.cli' in source
