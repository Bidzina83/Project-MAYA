import os
from subprocess import check_output


def test_memoryctl_list(tmp_path):
    storage = tmp_path / 'storage'
    storage.mkdir()
    regdir = storage / 'registry'
    regdir.mkdir()
    # write a simple registry
    reg = {
        'abc': {
            'chunk_id': 'abc',
            'embedding_path': str(storage / 'embeddings' / 'abc.json'),
            'source_path': '/tmp/x',
            'model': 'm',
            'provider': 'p',
            'vector_dim': 3,
            'embedding_timestamp': '2026-01-01T00:00:00Z'
        }
    }
    with open(regdir / 'memory_registry.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(reg, f)

    cli = os.path.join(os.path.dirname(__file__), '..', 'bin', 'memoryctl')
    cli = os.path.abspath(cli)
    out = check_output([cli, 'registry', 'list', '--storage-root', str(storage)], universal_newlines=True)
    assert 'abc' in out
    assert '\tm\t' in out
