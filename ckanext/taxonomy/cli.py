"""CKAN 2.10+ Click CLI commands for ckanext-taxonomy.

Usage:
    ckan -c <ini> taxonomy initdb
    ckan -c <ini> taxonomy seed-defaults -f <yaml_file> [--force] [--sync]
"""
import click


@click.group()
def taxonomy():
    """Taxonomy management commands."""
    pass


@taxonomy.command('initdb')
def initdb():
    """Create taxonomy database tables.

    Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
    """
    from ckanext.taxonomy.models import init_tables
    init_tables()
    click.echo("Taxonomy tables initialized.")


@taxonomy.command('seed-defaults')
@click.option('-f', '--file', 'filepath', required=True,
              type=click.Path(exists=True),
              help='Path to a YAML file with taxonomy definitions.')
@click.option('--force', is_flag=True, default=False,
              help='Clear all existing taxonomy data and re-seed.')
@click.option('--sync', is_flag=True, default=False,
              help='Add only missing taxonomies/terms without deleting existing data.')
def seed_defaults(filepath, force, sync):
    """Seed taxonomies and terms from a YAML file.

    Default: seeds only if taxonomy tables are empty.
    --force: clears all data first, then seeds.
    --sync:  adds missing items without duplicating existing ones.
    --force and --sync cannot be combined.
    """
    if force and sync:
        raise click.UsageError("--force and --sync are mutually exclusive.")

    from ckanext.taxonomy.seed import parse_yaml, seed_taxonomies

    taxonomies_data = parse_yaml(filepath)
    result = seed_taxonomies(taxonomies_data, force=force, sync=sync)
    if result:
        click.echo("Seed complete.")
    else:
        click.echo("Skipped: taxonomy tables already contain data. "
                    "Use --force or --sync.")


def get_commands():
    """Return the Click command group for CKAN CLI registration."""
    return [taxonomy]
