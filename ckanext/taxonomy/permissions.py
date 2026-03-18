import json
import logging

import ckan.model as model
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)

CONFIG_KEY = 'ckanext.taxonomy.orgs'


def _parse_org_whitelist():
    """Parse the org whitelist from CKAN config.

    Returns a list of org name strings, or ``['*']`` for wildcard.
    Supports:
      - comma-separated:  ``auscope-org,csiro-org``
      - single value:     ``auscope-org``
      - wildcard:         ``*``
      - JSON list:        ``["auscope-org", "csiro-org"]``
      - JSON wildcard:    ``["*"]``
    """
    raw = toolkit.config.get(CONFIG_KEY, '').strip()
    if not raw:
        return []

    # Try JSON list
    if raw.startswith('['):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except (json.JSONDecodeError, ValueError):
            pass

    # Comma-separated (also handles single value / wildcard)
    return [x.strip() for x in raw.split(',') if x.strip()]


def user_can_manage_taxonomy(user_name):
    """Check whether *user_name* is allowed to manage taxonomies.

    Returns ``True`` when any of the following is true:

    1. The user is a CKAN sysadmin.
    2. ``ckanext.taxonomy.orgs`` is configured **and** the user is an
       admin of at least one of the listed organisations (or any
       organisation when the value is ``*``).

    If no org whitelist is configured the function returns ``False`` for
    non-sysadmins, preserving the original sysadmin-only behaviour.
    """
    if not user_name:
        return False

    user = model.User.get(user_name)
    if not user:
        return False

    if user.sysadmin:
        return True

    orgs = _parse_org_whitelist()
    if not orgs:
        return False

    wildcard = '*' in orgs

    # Organisations where the user holds admin capacity
    admin_org_names = {
        row[0]
        for row in (
            model.Session.query(model.Group.name)
            .join(model.Member, model.Member.group_id == model.Group.id)
            .filter(
                model.Member.table_name == 'user',
                model.Member.table_id == user.id,
                model.Member.capacity == 'admin',
                model.Member.state == 'active',
                model.Group.is_organization == True,
                model.Group.state == 'active',
            )
        ).all()
    }

    if wildcard:
        return len(admin_org_names) > 0

    return bool(admin_org_names & set(orgs))
