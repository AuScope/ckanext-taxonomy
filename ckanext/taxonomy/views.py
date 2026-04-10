from flask import Blueprint
from ckanext.taxonomy.helpers import _normalise_parent_id

taxonomy_blueprint = Blueprint(
    'taxonomy', __name__,
)


# ── helpers ──────────────────────────────────────────────────────────

def _context():
    import ckan.model as model
    import ckan.plugins.toolkit as toolkit
    return {
        'model': model,
        'user': toolkit.g.user,
    }


def _check_admin():
    """Abort 403 if the current user is not a sysadmin."""
    import ckan.plugins.toolkit as toolkit
    try:
        toolkit.check_access('taxonomy_create', _context(), {})
    except toolkit.NotAuthorized:
        toolkit.abort(403, toolkit._('Not authorized'))


def _site_url():
    """Return the site's base URL (no trailing slash)."""
    import ckan.plugins.toolkit as toolkit
    return toolkit.config.get('ckan.site_url', '').rstrip('/')


# ── read views ───────────────────────────────────────────────────────

def index():
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    context = _context()
    taxonomies = logic.get_action('taxonomy_list')(context, {})

    # Build tree for each taxonomy
    taxonomy_trees = []
    for tax in taxonomies:
        terms = logic.get_action('taxonomy_term_tree')(
            context, {'id': tax['id']})
        taxonomy_trees.append({'taxonomy': tax, 'terms': terms})

    extra_vars = {
        'taxonomy_trees': taxonomy_trees,
        'is_admin': _is_admin(),
    }
    return toolkit.render('ckanext/taxonomy/index.html', extra_vars=extra_vars)


def taxonomy_detail(taxonomy_name):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    context = _context()
    tax = logic.get_action('taxonomy_show')(context, {'id': taxonomy_name})
    terms = logic.get_action('taxonomy_term_tree')(
        context, {'id': tax['id']})

    extra_vars = {
        'taxonomy': tax,
        'terms': terms,
        'is_admin': _is_admin(),
    }
    return toolkit.render('ckanext/taxonomy/taxonomy_detail.html',
                          extra_vars=extra_vars)


def term_detail(term_id):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    context = _context()
    term = logic.get_action('taxonomy_term_show')(context, {'id': term_id})
    tax = logic.get_action('taxonomy_show')(
        context, {'id': term['taxonomy_id']})

    # Get children
    all_terms = logic.get_action('taxonomy_term_list')(
        context, {'id': tax['id']})
    children = [t for t in all_terms if t['parent_id'] == term['id']]

    # Get parent label
    parent = None
    if term.get('parent_id'):
        try:
            parent = logic.get_action('taxonomy_term_show')(
                context, {'id': term['parent_id']})
        except logic.NotFound:
            pass

    extra_vars = {
        'term': term,
        'taxonomy': tax,
        'children': children,
        'parent': parent,
        'is_admin': _is_admin(),
    }
    return toolkit.render('ckanext/taxonomy/term_detail.html',
                          extra_vars=extra_vars)


# ── taxonomy CRUD ────────────────────────────────────────────────────

def taxonomy_create():
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    _check_admin()
    context = _context()

    if toolkit.request.method == 'POST':
        name = toolkit.request.form.get('name', '').strip()
        title = toolkit.request.form.get('title', '').strip()
        uri = toolkit.request.form.get('uri', '').strip()
        if not name:
            from ckan.lib.munge import munge_name
            name = munge_name(title)
        if not uri:
            uri = '{}/taxonomies/{}'.format(_site_url(), name)
        data = {'title': title, 'name': name, 'uri': uri}
        try:
            logic.get_action('taxonomy_create')(context, data)
            toolkit.h.flash_success(toolkit._('Taxonomy created'))
            return toolkit.redirect_to('taxonomy.index')
        except (logic.ValidationError, logic.NotFound) as e:
            error_msg = str(e)
            toolkit.h.flash_error(error_msg)

    return toolkit.render('ckanext/taxonomy/taxonomy_form.html',
                          extra_vars={'taxonomy': None, 'is_edit': False})


def taxonomy_edit(taxonomy_name):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    _check_admin()
    context = _context()

    tax = logic.get_action('taxonomy_show')(context, {'id': taxonomy_name})

    if toolkit.request.method == 'POST':
        name = toolkit.request.form.get('name', '').strip()
        uri = toolkit.request.form.get('uri', '').strip()
        if not uri:
            uri = '{}/taxonomies/{}'.format(_site_url(), name or tax['name'])
        data = {
            'id': tax['id'],
            'title': toolkit.request.form.get('title', '').strip(),
            'name': name,
            'uri': uri,
        }
        try:
            logic.get_action('taxonomy_update')(context, data)
            toolkit.h.flash_success(toolkit._('Taxonomy updated'))
            return toolkit.redirect_to('taxonomy.taxonomy_detail',
                                       taxonomy_name=data['name'])
        except (logic.ValidationError, logic.NotFound) as e:
            error_msg = str(e)
            toolkit.h.flash_error(error_msg)
            tax = data

    return toolkit.render('ckanext/taxonomy/taxonomy_form.html',
                          extra_vars={'taxonomy': tax, 'is_edit': True})


def taxonomy_delete_view(taxonomy_name):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    _check_admin()
    context = _context()

    tax = logic.get_action('taxonomy_show')(context, {'id': taxonomy_name})
    term_count = len(logic.get_action('taxonomy_term_list')(
        context, {'id': tax['id']}))

    if toolkit.request.method == 'POST':
        try:
            logic.get_action('taxonomy_delete')(context, {'id': tax['id']})
            toolkit.h.flash_success(toolkit._('Taxonomy deleted'))
            return toolkit.redirect_to('taxonomy.index')
        except (logic.ValidationError, logic.NotFound) as e:
            toolkit.h.flash_error(str(e))

    return toolkit.render('ckanext/taxonomy/confirm_delete.html',
                          extra_vars={
                              'item': tax,
                              'item_type': 'taxonomy',
                              'term_count': term_count,
                          })


# ── term CRUD ────────────────────────────────────────────────────────

def term_create(taxonomy_name):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    _check_admin()
    context = _context()

    tax = logic.get_action('taxonomy_show')(context, {'id': taxonomy_name})
    parent_id = _normalise_parent_id(toolkit.request.args.get('parent_id')) or ''

    if toolkit.request.method == 'POST':
        uri = toolkit.request.form.get('uri', '').strip()
        data = {
            'taxonomy_id': tax['id'],
            'label': toolkit.request.form.get('label', '').strip(),
            'uri': uri,
            'description': toolkit.request.form.get('description', '').strip(),
            'parent_id': _normalise_parent_id(toolkit.request.args.get('parent_id')) or '',
        }
        # Parse extras from form
        extras_str = toolkit.request.form.get('extras', '').strip()
        if extras_str:
            import json
            try:
                data['extras'] = json.loads(extras_str)
            except json.JSONDecodeError:
                toolkit.h.flash_error(toolkit._('Extras must be valid JSON'))
                return toolkit.render(
                    'ckanext/taxonomy/term_form.html',
                    extra_vars={
                        'taxonomy': tax, 'term': None,
                        'parent_id': data.get('parent_id', ''),
                        'is_edit': False,
                    })

        try:
            term = logic.get_action('taxonomy_term_create')(context, data)
            # Back-fill URI with site URL if it was left blank
            if not data.get('uri'):
                auto_uri = '{}/taxonomies/term/{}'.format(
                    _site_url(), term['id'])
                logic.get_action('taxonomy_term_update')(
                    context,
                    {'id': term['id'], 'uri': auto_uri})
            toolkit.h.flash_success(toolkit._('Term created'))
            return toolkit.redirect_to('taxonomy.term_detail',
                                       term_id=term['id'])
        except (logic.ValidationError, logic.NotFound) as e:
            toolkit.h.flash_error(str(e))

    return toolkit.render('ckanext/taxonomy/term_form.html',
                          extra_vars={
                              'taxonomy': tax,
                              'term': None,
                              'parent_id': parent_id,
                              'is_edit': False,
                          })


def term_edit(term_id):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    _check_admin()
    context = _context()

    term = logic.get_action('taxonomy_term_show')(context, {'id': term_id})
    tax = logic.get_action('taxonomy_show')(
        context, {'id': term['taxonomy_id']})

    if toolkit.request.method == 'POST':
        uri = toolkit.request.form.get('uri', '').strip()
        if not uri:
            uri = '{}/taxonomies/term/{}'.format(_site_url(), term['id'])
        data = {
            'id': term['id'],
            'label': toolkit.request.form.get('label', '').strip(),
            'uri': uri,
            'description': toolkit.request.form.get('description', '').strip(),
            'parent_id': _normalise_parent_id(toolkit.request.args.get('parent_id')) or '',
        }
        extras_str = toolkit.request.form.get('extras', '').strip()
        if extras_str:
            import json
            try:
                data['extras'] = json.loads(extras_str)
            except json.JSONDecodeError:
                toolkit.h.flash_error(toolkit._('Extras must be valid JSON'))
                return toolkit.render(
                    'ckanext/taxonomy/term_form.html',
                    extra_vars={
                        'taxonomy': tax, 'term': term,
                        'parent_id': term.get('parent_id', ''),
                        'is_edit': True,
                    })
        else:
            data['extras'] = None

        try:
            logic.get_action('taxonomy_term_update')(context, data)
            toolkit.h.flash_success(toolkit._('Term updated'))
            return toolkit.redirect_to('taxonomy.term_detail',
                                       term_id=term['id'])
        except (logic.ValidationError, logic.NotFound) as e:
            toolkit.h.flash_error(str(e))
            term.update(data)

    return toolkit.render('ckanext/taxonomy/term_form.html',
                          extra_vars={
                              'taxonomy': tax,
                              'term': term,
                              'parent_id': term.get('parent_id', ''),
                              'is_edit': True,
                          })


def term_delete_view(term_id):
    import ckan.logic as logic
    import ckan.plugins.toolkit as toolkit

    _check_admin()
    context = _context()

    term = logic.get_action('taxonomy_term_show')(context, {'id': term_id})
    tax = logic.get_action('taxonomy_show')(
        context, {'id': term['taxonomy_id']})

    # Count descendant terms
    all_terms = logic.get_action('taxonomy_term_list')(
        context, {'id': tax['id']})
    descendant_count = _count_descendants(term['id'], all_terms)

    if toolkit.request.method == 'POST':
        try:
            logic.get_action('taxonomy_term_delete')(
                context, {'id': term['id']})
            toolkit.h.flash_success(toolkit._('Term deleted'))
            return toolkit.redirect_to('taxonomy.taxonomy_detail',
                                       taxonomy_name=tax['name'])
        except (logic.ValidationError, logic.NotFound) as e:
            toolkit.h.flash_error(str(e))

    return toolkit.render('ckanext/taxonomy/confirm_delete.html',
                          extra_vars={
                              'item': term,
                              'item_type': 'term',
                              'taxonomy': tax,
                              'term_count': descendant_count,
                          })


def _count_descendants(term_id, all_terms):
    """Count all descendant terms recursively."""
    children = [t for t in all_terms if t['parent_id'] == term_id]
    count = len(children)
    for child in children:
        count += _count_descendants(child['id'], all_terms)
    return count


def _is_admin():
    """Check if the current user is a sysadmin without aborting."""
    import ckan.plugins.toolkit as toolkit
    try:
        toolkit.check_access('taxonomy_create', _context(), {})
        return True
    except toolkit.NotAuthorized:
        return False


# ── URL rules ────────────────────────────────────────────────────────

# Read
taxonomy_blueprint.add_url_rule(
    '/taxonomies', view_func=index, endpoint='index')
taxonomy_blueprint.add_url_rule(
    '/taxonomies/<taxonomy_name>',
    view_func=taxonomy_detail, endpoint='taxonomy_detail')
taxonomy_blueprint.add_url_rule(
    '/taxonomies/term/<term_id>',
    view_func=term_detail, endpoint='term_detail')

# Taxonomy CRUD
taxonomy_blueprint.add_url_rule(
    '/taxonomies/new', view_func=taxonomy_create,
    endpoint='taxonomy_create', methods=['GET', 'POST'])
taxonomy_blueprint.add_url_rule(
    '/taxonomies/<taxonomy_name>/edit', view_func=taxonomy_edit,
    endpoint='taxonomy_edit', methods=['GET', 'POST'])
taxonomy_blueprint.add_url_rule(
    '/taxonomies/<taxonomy_name>/delete', view_func=taxonomy_delete_view,
    endpoint='taxonomy_delete', methods=['GET', 'POST'])

# Term CRUD
taxonomy_blueprint.add_url_rule(
    '/taxonomies/<taxonomy_name>/term/new', view_func=term_create,
    endpoint='term_create', methods=['GET', 'POST'])
taxonomy_blueprint.add_url_rule(
    '/taxonomies/term/<term_id>/edit', view_func=term_edit,
    endpoint='term_edit', methods=['GET', 'POST'])
taxonomy_blueprint.add_url_rule(
    '/taxonomies/term/<term_id>/delete', view_func=term_delete_view,
    endpoint='term_delete', methods=['GET', 'POST'])
