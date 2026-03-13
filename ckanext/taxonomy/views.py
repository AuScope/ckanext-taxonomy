from flask import Blueprint

taxonomy_blueprint = Blueprint(
    'taxonomy', __name__,
)


def index():
    import ckan.logic as logic
    import ckan.model as model
    import ckan.plugins.toolkit as toolkit

    context = {
        'model': model,
        'user': toolkit.g.user,
    }
    taxonomies = logic.get_action('taxonomy_list')(context, {})
    extra_vars = {'taxonomies': taxonomies}
    return toolkit.render('ckanext/taxonomy/index.html', extra_vars=extra_vars)


def show(name):
    import ckan.logic as logic
    import ckan.model as model
    import ckan.plugins.toolkit as toolkit

    context = {
        'model': model,
        'user': toolkit.g.user,
    }
    tax = logic.get_action('taxonomy_show')(context, {'id': name})
    terms = logic.get_action('taxonomy_term_tree')(
        context, {'id': tax['id']})
    extra_vars = {'taxonomy': tax, 'terms': terms}
    return toolkit.render('ckanext/taxonomy/show.html', extra_vars=extra_vars)


taxonomy_blueprint.add_url_rule(
    '/taxonomies', view_func=index, endpoint='index')
taxonomy_blueprint.add_url_rule(
    '/taxonomies/<name>', view_func=show, endpoint='show')
