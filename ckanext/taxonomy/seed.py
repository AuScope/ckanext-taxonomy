"""YAML-based taxonomy seeding logic.

Parses a YAML file with taxonomy definitions and seeds them into the
database using the taxonomy models directly.
"""
import logging
import yaml

log = logging.getLogger(__name__)


def parse_yaml(filepath):
    """Parse a taxonomy YAML file and return the list of taxonomy dicts."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    if not data or 'taxonomies' not in data:
        raise ValueError("YAML file must contain a 'taxonomies' key")
    return data['taxonomies']


def seed_taxonomies(taxonomies_data, force=False, sync=False):
    """Seed taxonomy records from parsed YAML data.

    Args:
        taxonomies_data: list of taxonomy dicts from parse_yaml()
        force: if True, clear all existing data and re-seed
        sync: if True, add only missing taxonomies/terms
    """
    from ckanext.taxonomy.models import Taxonomy, TaxonomyTerm
    import ckan.model as model

    existing_count = model.Session.query(Taxonomy).count()

    if force:
        log.info("--force: clearing all taxonomy data")
        model.Session.query(TaxonomyTerm).delete()
        model.Session.query(Taxonomy).delete()
        model.Session.commit()
    elif existing_count > 0 and not sync:
        log.info(
            "Taxonomy tables already contain %d record(s). "
            "Use --force to clear and re-seed, or --sync to add missing items.",
            existing_count,
        )
        return False

    created_tax = 0
    created_terms = 0

    for tax_data in taxonomies_data:
        name = tax_data['name']
        existing = Taxonomy.get(name)

        if existing and sync:
            log.info("Taxonomy '%s' exists, syncing terms", name)
            tax_obj = existing
        elif existing and not sync:
            log.info("Taxonomy '%s' already exists, skipping", name)
            continue
        else:
            tax_obj = Taxonomy(
                name=name,
                title=tax_data.get('title', name),
                uri=tax_data.get('uri', ''),
            )
            model.Session.add(tax_obj)
            model.Session.flush()
            created_tax += 1
            log.info("Created taxonomy '%s'", name)

        terms_data = tax_data.get('terms', [])
        count = _create_terms_recursive(
            terms_data, tax_obj.id, parent_id=None, sync=sync,
        )
        created_terms += count

    model.Session.commit()
    log.info(
        "Seeding complete: %d taxonomies created, %d terms created",
        created_tax, created_terms,
    )
    return True


def _create_terms_recursive(terms_data, taxonomy_id, parent_id, sync):
    """Recursively create taxonomy terms. Returns count of terms created."""
    from ckanext.taxonomy.models import TaxonomyTerm
    import ckan.model as model

    count = 0
    for term_data in terms_data:
        label = term_data['label']
        uri = term_data.get('uri', '')
        description = term_data.get('description', '')
        extras = term_data.get('extras')

        existing = _find_existing_term(taxonomy_id, parent_id, label, uri)

        if existing:
            if sync:
                log.debug("Term '%s' already exists, skipping", label)
                term_id = existing.id
            else:
                term_id = existing.id
        else:
            term = TaxonomyTerm(
                label=label,
                uri=uri,
                description=description,
                extras=extras,
                taxonomy_id=taxonomy_id,
                parent_id=parent_id,
            )
            model.Session.add(term)
            model.Session.flush()
            term_id = term.id
            count += 1

        children = term_data.get('terms', [])
        if children:
            count += _create_terms_recursive(
                children, taxonomy_id, term_id, sync,
            )

    return count


def _find_existing_term(taxonomy_id, parent_id, label, uri):
    """Find an existing term by URI (preferred) or by (taxonomy, parent, label)."""
    from ckanext.taxonomy.models import TaxonomyTerm
    import ckan.model as model

    if uri:
        match = (
            model.Session.query(TaxonomyTerm)
            .filter(TaxonomyTerm.taxonomy_id == taxonomy_id)
            .filter(TaxonomyTerm.uri == uri)
            .first()
        )
        if match:
            return match

    return (
        model.Session.query(TaxonomyTerm)
        .filter(TaxonomyTerm.taxonomy_id == taxonomy_id)
        .filter(TaxonomyTerm.parent_id == parent_id)
        .filter(TaxonomyTerm.label == label)
        .first()
    )
