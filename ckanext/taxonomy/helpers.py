def _normalise_parent_id(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in ("", "None", "none", "null", "NULL"):
            return None
    return value


def taxonomy(named_taxonomy):
    """ Returns the named taxonomy """
    import ckan.model as model
    import ckan.logic as logic
    ctx = {'model': model}
    return logic.get_action('taxonomy_show')\
        (ctx, {'name': named_taxonomy})

def taxonomy_terms(taxonomy_id):
    import ckan.model as model
    import ckan.logic as logic
    ctx = {'model': model}
    return logic.get_action('taxonomy_term_tree')\
        (ctx, {'id': taxonomy_id})
