"""Tests for the org-whitelist permission logic.

These tests exercise ``permissions._parse_org_whitelist`` and
``permissions.user_can_manage_taxonomy`` using mocks so they run without
a full CKAN environment.  A small number of representative auth-function
tests confirm the wiring in ``auth.py``.
"""
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers to build mock objects
# ---------------------------------------------------------------------------

def _mock_user(name, sysadmin=False):
    user = MagicMock()
    user.name = name
    user.id = f'user-id-{name}'
    user.sysadmin = sysadmin
    return user


def _mock_query_result(org_names):
    """Return a mock query whose ``.all()`` yields ``[(name,)]`` tuples."""
    rows = [(n,) for n in org_names]
    query = MagicMock()
    query.join.return_value = query
    query.filter.return_value = query
    query.all.return_value = rows
    return query


# ---------------------------------------------------------------------------
# _parse_org_whitelist
# ---------------------------------------------------------------------------

class TestParseOrgWhitelist:

    def _call(self, config_value):
        with patch('ckanext.taxonomy.permissions.toolkit') as mock_tk:
            mock_tk.config.get.return_value = config_value
            from ckanext.taxonomy.permissions import _parse_org_whitelist
            return _parse_org_whitelist()

    def test_empty_string(self):
        assert self._call('') == []

    def test_none_coerced(self):
        """config.get returns '' for missing key, but be safe."""
        with patch('ckanext.taxonomy.permissions.toolkit') as mock_tk:
            mock_tk.config.get.return_value = ''
            from ckanext.taxonomy.permissions import _parse_org_whitelist
            assert _parse_org_whitelist() == []

    def test_single_org(self):
        assert self._call('auscope-org') == ['auscope-org']

    def test_multiple_orgs_comma(self):
        assert self._call('auscope-org,csiro-org') == ['auscope-org', 'csiro-org']

    def test_multiple_orgs_spaces(self):
        assert self._call(' auscope-org , csiro-org ') == ['auscope-org', 'csiro-org']

    def test_wildcard(self):
        assert self._call('*') == ['*']

    def test_json_list(self):
        assert self._call('["auscope-org", "csiro-org"]') == ['auscope-org', 'csiro-org']

    def test_json_wildcard(self):
        assert self._call('["*"]') == ['*']

    def test_malformed_json_falls_back_to_csv(self):
        result = self._call('[bad json')
        # Falls through to comma-split; square bracket kept in first token
        assert len(result) >= 1

    def test_whitespace_only(self):
        assert self._call('   ') == []


# ---------------------------------------------------------------------------
# user_can_manage_taxonomy
# ---------------------------------------------------------------------------

class TestUserCanManageTaxonomy:

    def _patches(self, config_value='', user=None, admin_org_names=None):
        """Return a context-manager stack patching toolkit, model."""
        import contextlib

        @contextlib.contextmanager
        def _ctx():
            with patch('ckanext.taxonomy.permissions.toolkit') as mock_tk, \
                 patch('ckanext.taxonomy.permissions.model') as mock_model:
                mock_tk.config.get.return_value = config_value
                mock_model.User.get.return_value = user
                mock_model.Session.query.return_value = \
                    _mock_query_result(admin_org_names or [])
                # Expose model.Group, model.Member so the join/filter
                # expressions don't blow up with attribute errors.
                mock_model.Group = MagicMock()
                mock_model.Member = MagicMock()
                yield mock_tk, mock_model

        return _ctx()

    # 1. Sysadmin always allowed
    def test_sysadmin_allowed_no_config(self):
        user = _mock_user('admin', sysadmin=True)
        with self._patches(config_value='', user=user):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('admin') is True

    def test_sysadmin_allowed_with_config(self):
        user = _mock_user('admin', sysadmin=True)
        with self._patches(config_value='some-org', user=user):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('admin') is True

    # 2. No config -> default sysadmin-only behaviour preserved
    def test_no_config_non_sysadmin_denied(self):
        user = _mock_user('bob', sysadmin=False)
        with self._patches(config_value='', user=user):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('bob') is False

    # 3. Single whitelisted org admin allowed
    def test_single_org_admin_allowed(self):
        user = _mock_user('alice', sysadmin=False)
        with self._patches(config_value='auscope-org', user=user,
                           admin_org_names=['auscope-org']):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('alice') is True

    # 4. User not admin of whitelisted org -> denied
    def test_non_admin_of_whitelisted_org_denied(self):
        user = _mock_user('carol', sysadmin=False)
        with self._patches(config_value='auscope-org', user=user,
                           admin_org_names=['other-org']):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('carol') is False

    # 5. Multiple whitelisted orgs
    def test_multiple_whitelisted_orgs(self):
        user = _mock_user('dave', sysadmin=False)
        with self._patches(config_value='auscope-org,csiro-org', user=user,
                           admin_org_names=['csiro-org']):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('dave') is True

    def test_multiple_whitelisted_orgs_no_match(self):
        user = _mock_user('eve', sysadmin=False)
        with self._patches(config_value='auscope-org,csiro-org', user=user,
                           admin_org_names=['third-org']):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('eve') is False

    # 6. Wildcard allows admin of any org
    def test_wildcard_admin_of_any_org_allowed(self):
        user = _mock_user('frank', sysadmin=False)
        with self._patches(config_value='*', user=user,
                           admin_org_names=['random-org']):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('frank') is True

    def test_wildcard_no_org_membership_denied(self):
        user = _mock_user('grace', sysadmin=False)
        with self._patches(config_value='*', user=user,
                           admin_org_names=[]):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('grace') is False

    # 7. Non-admin org member denied (they have memberships but as non-admin;
    #    the query only returns admin-capacity memberships, so the result
    #    set is empty)
    def test_org_member_non_admin_denied(self):
        user = _mock_user('heidi', sysadmin=False)
        # The query mock returns [] because the real query filters capacity='admin'
        with self._patches(config_value='auscope-org', user=user,
                           admin_org_names=[]):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('heidi') is False

    # 8. Edge cases
    def test_empty_username(self):
        with self._patches():
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('') is False

    def test_none_username(self):
        with self._patches():
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy(None) is False

    def test_unknown_user(self):
        with self._patches(config_value='auscope-org', user=None):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            assert user_can_manage_taxonomy('ghost') is False

    # 9. Malformed config handled safely
    def test_malformed_config_denied(self):
        user = _mock_user('ivan', sysadmin=False)
        with self._patches(config_value='[bad json', user=user,
                           admin_org_names=[]):
            from ckanext.taxonomy.permissions import user_can_manage_taxonomy
            # Malformed JSON falls back to comma-split; '[bad json' won't
            # match any real org name, so the user is denied.
            assert user_can_manage_taxonomy('ivan') is False


# ---------------------------------------------------------------------------
# Auth function wiring (representative sample)
# ---------------------------------------------------------------------------

class TestAuthWiring:
    """Verify that auth functions delegate to user_can_manage_taxonomy."""

    def test_taxonomy_create_delegates(self):
        with patch('ckanext.taxonomy.auth.user_can_manage_taxonomy',
                   return_value=True) as mock_perm:
            from ckanext.taxonomy.auth import taxonomy_create
            result = taxonomy_create(context={'user': 'someone'}, data_dict={})
            assert result == {'success': True}
            mock_perm.assert_called_once_with('someone')

    def test_taxonomy_create_denied(self):
        with patch('ckanext.taxonomy.auth.user_can_manage_taxonomy',
                   return_value=False) as mock_perm:
            from ckanext.taxonomy.auth import taxonomy_create
            result = taxonomy_create(context={'user': 'nobody'}, data_dict={})
            assert result == {'success': False}
            mock_perm.assert_called_once_with('nobody')

    def test_taxonomy_delete_delegates(self):
        with patch('ckanext.taxonomy.auth.user_can_manage_taxonomy',
                   return_value=True):
            from ckanext.taxonomy.auth import taxonomy_delete
            result = taxonomy_delete(context={'user': 'someone'}, data_dict={})
            assert result == {'success': True}

    def test_taxonomy_term_create_delegates(self):
        with patch('ckanext.taxonomy.auth.user_can_manage_taxonomy',
                   return_value=True):
            from ckanext.taxonomy.auth import taxonomy_term_create
            result = taxonomy_term_create(context={'user': 'someone'}, data_dict={})
            assert result == {'success': True}

    def test_taxonomy_term_update_delegates(self):
        with patch('ckanext.taxonomy.auth.user_can_manage_taxonomy',
                   return_value=False):
            from ckanext.taxonomy.auth import taxonomy_term_update
            result = taxonomy_term_update(context={'user': 'x'}, data_dict={})
            assert result == {'success': False}

    def test_taxonomy_term_delete_delegates(self):
        with patch('ckanext.taxonomy.auth.user_can_manage_taxonomy',
                   return_value=True):
            from ckanext.taxonomy.auth import taxonomy_term_delete
            result = taxonomy_term_delete(context={'user': 'someone'}, data_dict={})
            assert result == {'success': True}

    # Read auth functions remain unchanged
    def test_taxonomy_list_always_allowed(self):
        from ckanext.taxonomy.auth import taxonomy_list
        assert taxonomy_list(context={}, data_dict={}) == {'success': True}

    def test_taxonomy_show_always_allowed(self):
        from ckanext.taxonomy.auth import taxonomy_show
        assert taxonomy_show(context={}, data_dict={}) == {'success': True}

    def test_taxonomy_term_show_always_allowed(self):
        from ckanext.taxonomy.auth import taxonomy_term_show
        assert taxonomy_term_show(context={}, data_dict={}) == {'success': True}
