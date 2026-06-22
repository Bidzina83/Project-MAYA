import unittest

class InMemoryBackend:
    """Tiny in-memory backend used by unit tests in this workspace.
    This is a placeholder for the project's real memory adapter; tests exercise
    the CRUD contract and can be run with Python's standard library unittest.
    """
    def __init__(self):
        self.store = {}

    def create(self, key, value):
        self.store[key] = value

    def read(self, key):
        return self.store.get(key)

    def update(self, key, value):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class TestMemoryInterface(unittest.TestCase):
    def test_crud(self):
        backend = InMemoryBackend()

        # initially absent
        self.assertIsNone(backend.read("foo"))

        # create + read
        backend.create("foo", {"v": 1})
        self.assertEqual(backend.read("foo"), {"v": 1})

        # update
        backend.update("foo", {"v": 2})
        self.assertEqual(backend.read("foo"), {"v": 2})

        # delete
        backend.delete("foo")
        self.assertIsNone(backend.read("foo"))


if __name__ == "__main__":
    unittest.main()
