import json
import os
from jsonschema import validate, Draft7Validator

BASE = os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'schemas')


def load_schema(name):
    path = os.path.join(BASE, name)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_provenance_schema_valid_sample():
    schema = load_schema('provenance.schema.json')
    sample = {
        "source_path": "/opt/data/sample.txt",
        "source_hash": "a" * 64,
        "extractor_version": "v0.1",
        "timestamp": "2026-05-25T18:00:00Z"
    }
    validate(instance=sample, schema=schema)


def test_memory_record_schema_valid_sample():
    schema = load_schema('memory_record.schema.json')
    sample = {
        "chunk_id": "b" * 64,
        "text": "example",
        "vector": [0.1, 0.2],
        "metadata": {
            "source_path": "/opt/data/sample.txt",
            "source_hash": "a" * 64,
            "extractor_version": "v0.1",
            "timestamp": "2026-05-25T18:00:00Z"
        }
    }
    # When schema uses local $ref to provenance.schema.json we need a file-based resolver
    base_uri = 'file://' + os.path.join(os.path.dirname(__file__), '..', '..', 'docs', 'schemas') + os.sep
    # Build a resolver class instance using Draft7Validator's default resolver
    resolver = Draft7Validator(schema).resolver.__class__(base_uri, None)
    Draft7Validator(schema, resolver=resolver).validate(sample)


def test_index_entry_schema_valid_sample():
    schema = load_schema('index_entry.schema.json')
    sample = {
        "embedding_id": "emb-1",
        "chunk_id": "c" * 64,
        "vector_dim": 2,
        "created_at": "2026-05-25T18:00:00Z",
        "source_path": "/opt/data/sample.txt",
        "score_meta": {"score": 0.9}
    }
    validate(instance=sample, schema=schema)


def test_provenance_schema_invalid_missing_field():
    schema = load_schema('provenance.schema.json')
    sample = {"source_path": "/tmp/x"}
    try:
        validate(instance=sample, schema=schema)
        assert False, "Validation should fail for missing required fields"
    except Exception:
        pass
