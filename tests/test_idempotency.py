from __future__ import annotations

import unittest

from usecasecore import IdempotencyConflict, InMemoryIdempotencyStore


class InMemoryIdempotencyStoreTests(unittest.TestCase):
    def test_returns_saved_result(self) -> None:
        store = InMemoryIdempotencyStore()

        store.save("key-1", {"ok": True})

        self.assertEqual(store.get("key-1"), {"ok": True})

    def test_rejects_conflicting_result(self) -> None:
        store = InMemoryIdempotencyStore()
        store.save("key-1", {"ok": True})

        with self.assertRaises(IdempotencyConflict):
            store.save("key-1", {"ok": False})
