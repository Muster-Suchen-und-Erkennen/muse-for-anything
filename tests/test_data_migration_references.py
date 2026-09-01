from muse_for_anything.json_migrations import DataMigrator, JsonSchema

_ROOT_URL = "http://localhost:5000/test-schemas/"


def test_simple_to_ref():
    start = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"type": ["string"]}},
                    "type": ["object"],
                }
            },
            "title": "Type",
        },
    )
    target = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"$ref": "#/definitions/nested"}},
                    "type": ["object"],
                },
                "nested": {
                    "type": ["string"],
                },
            },
            "title": "Type",
        },
    )
    data = {"prop": "Hello world!"}
    assert DataMigrator.check_schema_changes(start, target)
    updated_data = DataMigrator.migrate_data(data, start, target)
    assert data == updated_data


def test_ref_to_simple():
    start = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"$ref": "#/definitions/nested"}},
                    "type": ["object"],
                },
                "nested": {
                    "type": ["string"],
                },
            },
            "title": "Type",
        },
    )
    target = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"type": ["string"]}},
                    "type": ["object"],
                }
            },
            "title": "Type",
        },
    )
    data = {"prop": "Hello world!"}
    assert DataMigrator.check_schema_changes(start, target)
    updated_data = DataMigrator.migrate_data(data, start, target)
    assert data == updated_data


def test_ref_to_ref():
    start = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"$ref": "#/definitions/nested"}},
                    "type": ["object"],
                },
                "nested": {
                    "type": ["string"],
                    "minLength": 3,
                },
            },
            "title": "Type",
        },
    )
    target = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"$ref": "#/definitions/nested"}},
                    "type": ["object"],
                },
                "nested": {
                    "type": ["string"],
                },
            },
            "title": "Type",
        },
    )
    data = {"prop": "Hello world!"}
    assert DataMigrator.check_schema_changes(start, target)
    updated_data = DataMigrator.migrate_data(data, start, target)
    assert data == updated_data


def test_ref_to_ref_w_type_change():
    start = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"$ref": "#/definitions/nested"}},
                    "type": ["object"],
                },
                "nested": {
                    "type": ["integer"],
                },
            },
            "title": "Type",
        },
    )
    target = JsonSchema(
        _ROOT_URL,
        {
            "$ref": "#/definitions/root",
            "$schema": "http://json-schema.org/draft-07/schema#",
            "abstract": False,
            "definitions": {
                "root": {
                    "properties": {"prop": {"$ref": "#/definitions/nested"}},
                    "type": ["object"],
                },
                "nested": {
                    "type": ["string"],
                },
            },
            "title": "Type",
        },
    )
    data = {"prop": 42}
    assert DataMigrator.check_schema_changes(start, target)
    updated_data = DataMigrator.migrate_data(data, start, target)
    assert {"prop": "42"} == updated_data
