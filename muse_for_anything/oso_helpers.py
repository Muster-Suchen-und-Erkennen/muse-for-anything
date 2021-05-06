"""Module for setting up oso support for flask app."""

from flask import Flask
from flask_oso import FlaskOso
from oso import Oso

OSO = Oso()

FLASK_OSO = FlaskOso(oso=OSO)


def register_oso(app: Flask):
    """Register oso to enable access management for this app."""
    from .db.models.users import User
    from .db.models.namespace import Namespace
    from .db.models.ontology_objects import (
        OntologyObjectType,
        OntologyObjectTypeVersion,
        OntologyObject,
        OntologyObjectVersion,
    )
    from .db.models.taxonomies import (
        Taxonomy,
        TaxonomyItem,
        TaxonomyItemVersion,
        TaxonomyItemRelation,
    )

    FLASK_OSO.init_app(app)

    # Uncomment to enable fail fast on unchecked enpoints
    # FLASK_OSO.require_authorization(app)

    oso_classes = (
        User,
        Namespace,
        OntologyObjectType,
        OntologyObjectTypeVersion,
        OntologyObject,
        OntologyObjectVersion,
        Taxonomy,
        TaxonomyItem,
        TaxonomyItemVersion,
        TaxonomyItemRelation,
    )
    for class_to_register in oso_classes:
        OSO.register_class(class_to_register)

    for policy in app.config.get("OSO_POLICY_FILES", []):
        OSO.load_file(policy)
