from setuptools import setup, find_packages

setup(
    name='ckanext-taxonomy',
    version="1.1.0",
    author='Ross Jones',
    author_email='ross@servercode.co.uk',
    license='AGPL-3.0',
    url='http://github.com/datagovuk/ckanext-taxonomy',
    description="Hierarchical 'tags'.",
    keywords="taxonomy hierarchy",
    long_description="",
    zip_safe=False,
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.8',
    install_requires=[
        'rdflib>=6.0.0',
    ],
    extras_require={
        'dev': ['pytest'],
    },
    entry_points={
        'paste.paster_command': [
            'taxonomy = ckanext.taxonomy.commands:TaxonomyCommand',
        ],
        'ckan.plugins': [
            'taxonomy = ckanext.taxonomy.plugin:TaxonomyPlugin',
        ],
    },
)
