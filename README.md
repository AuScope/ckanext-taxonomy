# ckanext-taxonomy

A CKAN extension that provides hierarchical taxonomies (structured vocabularies) as an alternative to CKAN's flat tag vocabularies.

Features:

- Terms belong to a named taxonomy
- Terms support parent/child hierarchy
- Each term has a label, URI, and optional description
- Taxonomies can be loaded from [SKOS](http://www.w3.org/2004/02/skos/specs) RDF documents
- Full CRUD API for taxonomies and terms
- **Admin UI** with tree view, detail pages, and inline create/edit/delete
- **Taxonomies** navigation tab in the CKAN header

Detailed API documentation is in [API.md](API.md).

## Installation

### From a local clone (recommended for Docker)

```bash
pip install /path/to/ckanext-taxonomy
```

### From source in development mode

```bash
cd ckanext-taxonomy
pip install -e ".[dev]"
```

### Integration with CKAN

1. Add `taxonomy` to `ckan.plugins` in your CKAN config file:

    ```ini
    ckan.plugins = ... taxonomy
    ```

2. Initialize the database tables:

    ```bash
    ckan -c /etc/ckan/production.ini taxonomy initdb
    ```

    (Legacy paster equivalent: `paster taxonomy init -c /etc/ckan/production.ini`)

## Command-line cheat sheet

### Click CLI (CKAN 2.10+)

| Command | Description |
|---------|-------------|
| `ckan -c <INI> taxonomy initdb` | Create taxonomy database tables (idempotent) |
| `ckan -c <INI> taxonomy seed-defaults -f <YAML>` | Seed taxonomies from a YAML file (skips if data exists) |
| `ckan -c <INI> taxonomy seed-defaults -f <YAML> --force` | Clear all taxonomy data, then re-seed from YAML |
| `ckan -c <INI> taxonomy seed-defaults -f <YAML> --sync` | Add only missing taxonomies/terms from YAML |

### Seed YAML format

```yaml
taxonomies:
  - name: topics
    title: Topics
    uri: http://example.com/topics
    terms:
      - label: Science
        uri: http://example.com/topics/science
        terms:
          - label: Physics
          - label: Chemistry
      - label: Arts
```

### Legacy paster CLI

| Command | Description |
|---------|-------------|
| `paster taxonomy init -c <CONFIG>` | Create taxonomy database tables |
| `paster taxonomy cleanup -c <CONFIG>` | Drop taxonomy database tables |
| `paster taxonomy load --filename <FILE> --name <NAME> --title <TITLE> --uri <URI> [-c <CONFIG>]` | Load a SKOS taxonomy from a local file |
| `paster taxonomy load --url <URL> --name <NAME> --title <TITLE> --uri <URI> [-c <CONFIG>]` | Load a SKOS taxonomy from a URL |
| `paster taxonomy load --lang <LANG> ...` | Specify language for labels (default: `en`) |
| `paster taxonomy load-extras --filename <FILE> --name <NAME> [-c <CONFIG>]` | Load extra metadata for existing terms from a JSON file |

## API cheat sheet

All actions are available via `/api/3/action/<ACTION>`.

| Action | Methods | Key arguments |
|--------|---------|---------------|
| `taxonomy_list` | GET, POST | — |
| `taxonomy_show` | GET, POST | `id` or `uri` |
| `taxonomy_create` | POST | `title`, `name`, `uri` |
| `taxonomy_update` | POST | `id`, `title`, `name`, `uri` |
| `taxonomy_delete` | POST | `id` |
| `taxonomy_term_list` | GET, POST | `id` (taxonomy) |
| `taxonomy_term_tree` | GET, POST | `id` (taxonomy) |
| `taxonomy_term_show` | GET, POST | `id` or `uri` |
| `taxonomy_term_show_bulk` | GET, POST | `uris` (list) |
| `taxonomy_term_create` | POST | `taxonomy_id`, `label`, `uri` |
| `taxonomy_term_update` | POST | `id`, `uri` |
| `taxonomy_term_delete` | POST | `id` |

## Admin Web UI

The extension includes a built-in admin UI for managing taxonomies, accessible via the **Taxonomies** tab in the CKAN header navigation.

### Pages

| URL | Description |
|-----|-------------|
| `/taxonomies` | **Tree view** — all taxonomies with expandable term hierarchies |
| `/taxonomies/<name>` | **Taxonomy detail** — info table + full term tree |
| `/taxonomies/term/<id>` | **Term detail** — label, URI, description, parent, children, extras |
| `/taxonomies/new` | Create a new taxonomy (admin only) |
| `/taxonomies/<name>/edit` | Edit a taxonomy (admin only) |
| `/taxonomies/<name>/delete` | Delete a taxonomy with confirmation (admin only) |
| `/taxonomies/<name>/term/new` | Create a new term (admin only) |
| `/taxonomies/term/<id>/edit` | Edit a term (admin only) |
| `/taxonomies/term/<id>/delete` | Delete a term with confirmation (admin only) |

### Features

- **Tree view** with expand/collapse and clickable labels linking to detail pages
- **Action buttons** (Add, Edit, Delete) appear on hover for admin users
- **Delete confirmation** shows the count of child terms that will be recursively deleted
- **Navigation tab** added to the CKAN header automatically when the plugin is enabled
- Read pages are accessible to all users; create/edit/delete require sysadmin

## Importing SKOS documents

> **Warning**: Loading a taxonomy will delete any existing taxonomy with the same name.

```bash
# DGU themes (file included in repo)
paster taxonomy load --filename dgu-themes.rdf --name dgu --title "DGU Themes" \
    --uri "http://data.gov.uk/themes" -c /etc/ckan/production.ini

# COFOG from local file
paster taxonomy load --filename COFOG.rdf --name cofog --title cofog \
    --uri "http://unstats.un.org/unsd/cr/registry/regcst.asp?Cl=4" -c /etc/ckan/production.ini

# From a URL
paster taxonomy load --url http://example.com/vocab.rdf --name myvocab \
    --title "My Vocab" --uri "http://example.com/vocab" -c /etc/ckan/production.ini
```

## Running tests

Tests run inside Docker — no local Python environment needed.

### Quick run (PowerShell)

```powershell
.\run_tests.ps1
```

### Manual Docker run

```bash
docker build -f Dockerfile.test -t ckanext-taxonomy-test .
docker run --rm ckanext-taxonomy-test
```

The test suite covers the vendored SKOS loader (`test_skos_loader.py`), Flask blueprint wiring and admin routes (`test_views.py`), and Click CLI structure and YAML parsing (`test_cli.py`). Tests that depend on a full CKAN environment (actions, models, auth, seed logic) require running inside a CKAN Docker container with a database.

## Removing the extension

1. Drop the database tables:

    ```bash
    # Legacy paster (no Click equivalent yet):
    paster taxonomy cleanup -c /etc/ckan/production.ini
    ```

2. Remove `taxonomy` from `ckan.plugins` in your config file.

## Modernization notes

This fork has been updated from the original `datagovuk/ckanext-taxonomy` to work with modern Python (3.8+) and CKAN 2.11:

| Area | Before | After |
|------|--------|-------|
| Python | 2.7 syntax (`print`, `.iteritems()`, `unicode()`) | Python 3 |
| `rdflib` | Pinned `==4.1.2` (broken on Python 3.10+, `distutils.run_2to3` error) | `>=6.0.0` |
| `python-skos` | Pinned `==0.1.1` via git `dependency_links` (abandoned, not on PyPI) | Replaced with vendored `skos_loader.py` (~70 lines using rdflib directly) |
| Packaging | `ez_setup` fallback, `namespace_packages`, `dependency_links` | Minimal `setup.py` + `pyproject.toml` with `setuptools.build_meta` |
| Install | Required `pip install -e "git+..."` | Standard `pip install .` from source tree |
| Routing | Pylons `IRoutes` + `BaseController` (removed in CKAN 2.10) | Flask `IBlueprint` + view functions in `views.py` |
| Templates | `h.nav_link(controller=..., action=...)` and `c.*` globals | `h.url_for('taxonomy.index')` and extra_vars |
| CLI | `paster` commands only | Click CLI (`IClick`) + legacy paster via compatibility layer |
| Seed data | Manual API calls or SKOS RDF only | YAML seed files via `ckan taxonomy seed-defaults` |
| Admin UI | None (API only) | Built-in tree view, detail pages, and CRUD forms |
| Tests | `nosetests` | `pytest` via Docker |

### Known follow-up items

- `ckanext/__init__.py` still uses `pkg_resources.declare_namespace()` — works but emits deprecation warnings. Can be replaced with implicit namespace packages.
- The old `controllers.py` is still present in the tree but no longer used by the plugin. It can be removed once migration is confirmed stable.
- The old paster `commands.py` is still present for backward compatibility via CKAN's paster shim. The preferred CLI is now Click-based (`cli.py`).

## License

AGPL-3.0 — see [LICENSE.md](LICENSE.md).
