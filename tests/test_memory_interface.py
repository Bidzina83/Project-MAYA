import unittest

from project_maya.memory import MemoryRetriever


class FakeRetriever:
    def __init__(self):
        self.documents = {}

    def upsert(self, doc):
        memory_id = doc.get("id") or doc.get("chunk_id") or doc.get("embedding_id")
        self.documents[memory_id] = dict(doc)

    def bulk_upsert(self, docs):
        for doc in docs:
            self.upsert(doc)

    def get(self, id):
        return self.documents.get(id)

    def query_vector(self, vector, top_k=10, metric="cosine"):
        return list(self.documents.values())[:top_k]

    def search(self, query, category=None, limit=10):
        matches = [
            doc
            for doc in self.documents.values()
            if query.lower() in doc.get("content", "").lower()
            and (category is None or doc.get("category") == category)
        ]
        return matches[:limit]

    def probe(self, entity, category=None, limit=10):
        return self.search(entity, category, limit)

    def related(self, entity, category=None, limit=10):
        return self.search(entity, category, limit)

    def reason(self, entities, category=None, limit=10):
        return self.search(" ".join(entities), category, limit)

    def contradict(self, category=None, threshold=0.3, limit=10):
        return []

    def stats(self):
        return {"count": len(self.documents)}


class TestMemoryInterface(unittest.TestCase):
    def test_public_vocabulary_delegates_to_retriever_contract(self):
        memory = MemoryRetriever(FakeRetriever())
        document = {
            "id": "greeting",
            "content": "hello from persistent memory",
            "category": "general",
        }

        memory.remember(document)

        self.assertEqual(memory.recall("greeting"), document)
        self.assertEqual(memory.search("persistent"), [document])

    def test_remember_requires_stable_identifier(self):
        memory = MemoryRetriever(FakeRetriever())

        with self.assertRaisesRegex(ValueError, "requires id"):
            memory.remember({"content": "not addressable"})

    def test_rejects_key_value_stub_as_retriever(self):
        class KeyValueBackend:
            def read(self, key):
                return None

            def write(self, key, value):
                return True

        with self.assertRaisesRegex(TypeError, "Retriever contract"):
            MemoryRetriever(KeyValueBackend())


if __name__ == "__main__":
    unittest.main()
