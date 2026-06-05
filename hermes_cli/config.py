def cfg_get(cfg, *keys, default=None):
    """Minimal shim of cfg_get for CI: traverse dict-like cfg and return nested value or default.

    This is a test-support shim when hermes_cli is not available in the environment.
    It preserves the signature used in plugins and returns `default` when the path
    doesn't exist or cfg is None.
    """
    if cfg is None:
        return default
    cur = cfg
    for k in keys:
        try:
            if isinstance(cur, dict):
                cur = cur.get(k, default)
            else:
                return default
        except Exception:
            return default
    return cur

# Optional helpers used in some imports (lightweight stubs)
def load_config(path):
    try:
        import json
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(path, cfg):
    try:
        import json
        with open(path, 'w') as f:
            json.dump(cfg, f, indent=2)
        return True
    except Exception:
        return False
