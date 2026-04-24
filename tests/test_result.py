from __future__ import annotations

import unittest

from usecasecore import Result


class ResultTests(unittest.TestCase):
    def test_can_accumulate_metadata_without_mutating_original(self) -> None:
        result = Result.ok("done")

        updated = result.with_event("InventoryMoved").with_job("LowStockAlert")

        self.assertEqual(result.events, ())
        self.assertEqual(result.jobs, ())
        self.assertEqual(updated.events, ("InventoryMoved",))
        self.assertEqual(updated.jobs, ("LowStockAlert",))
