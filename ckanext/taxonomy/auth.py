from ckan.logic import auth_allow_anonymous_access

from ckanext.taxonomy.permissions import user_can_manage_taxonomy


def _check_manage(context):
    """Return an auth-result dict based on the org-whitelist permission helper."""
    user = context.get('user', '') if context else ''
    return {'success': user_can_manage_taxonomy(user)}


@auth_allow_anonymous_access
def taxonomy_list(context=None, data_dict=None):
    """
    Does the user have permission to list the taxonomies available.
    This is always yes.
    """
    return {'success': True}


@auth_allow_anonymous_access
def taxonomy_show(context=None, data_dict=None):
    """
    Can the user view a specific taxonomy
    This is always yes.
    """
    return {'success': True}


@auth_allow_anonymous_access
def taxonomy_create(context=None, data_dict=None):
    """
    Can the user create a new taxonomy.

    Allowed for sysadmins and admins of whitelisted organisations
    (configured via ``ckanext.admin.orgs``).
    """
    return _check_manage(context)


@auth_allow_anonymous_access
def taxonomy_update(context=None, data_dict=None):
    """
    Can the user update an existing taxonomy.

    Allowed for sysadmins and admins of whitelisted organisations.
    """
    return _check_manage(context)


@auth_allow_anonymous_access
def taxonomy_delete(context=None, data_dict=None):
    """
    Can a user delete a taxonomy.

    Allowed for sysadmins and admins of whitelisted organisations.
    """
    return _check_manage(context)


@auth_allow_anonymous_access
def taxonomy_term_list(context=None, data_dict=None):
    """
    Can a user list taxonomy terms.
    """
    return {'success': True}


@auth_allow_anonymous_access
def taxonomy_term_tree(context=None, data_dict=None):
    """
    Can a user retrieve the terms for a taxonomy as a tree.
    """
    return {'success': True}


@auth_allow_anonymous_access
def taxonomy_term_show(context=None, data_dict=None):
    """
    Can a user view a taxonomy term (and the items using it)
    """
    return {'success': True}


@auth_allow_anonymous_access
def taxonomy_term_create(context=None, data_dict=None):
    """
    Can a user create a new taxonomy term.

    Allowed for sysadmins and admins of whitelisted organisations.
    """
    return _check_manage(context)


@auth_allow_anonymous_access
def taxonomy_term_update(context=None, data_dict=None):
    """
    Can a user update an existing term.

    Allowed for sysadmins and admins of whitelisted organisations.
    """
    return _check_manage(context)


@auth_allow_anonymous_access
def taxonomy_term_delete(context=None, data_dict=None):
    """
    Can a user delete a taxonomy term.

    Allowed for sysadmins and admins of whitelisted organisations.
    """
    return _check_manage(context)
