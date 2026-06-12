import unittest
from src.geometry import Position, Item, PackedItem, Container


class TestGeometry(unittest.TestCase):
    def setUp(self):
        self.container = Container(width=10, height=10, depth=10, max_weight=100.0)
        self.item_a = Item("BoxA", width=3, height=3, depth=3, weight=10.0)
        self.item_b = Item("BoxB", width=2, height=2, depth=2, weight=5.0)

    def test_item_properties(self):
        self.assertEqual(self.item_a.volume, 27.0)
        self.assertEqual(len(self.item_a.get_all_orientations()), 1)

        item_c = Item("BoxC", 3, 3, 4)
        self.assertEqual(len(item_c.get_all_orientations()), 3)

    def test_container_fits(self):
        pos = Position(0, 0, 0)
        self.assertTrue(self.container.fits_inside(pos, 3, 3, 3))
        self.assertFalse(self.container.fits_inside(pos, 11, 3, 3))

    def test_collision(self):
        self.assertTrue(
            self.container.add_item(self.item_a, Position(0, 0, 0), 3, 3, 3)
        )

        self.assertFalse(
            self.container.add_item(self.item_b, Position(2, 2, 2), 2, 2, 2)
        )

        self.assertTrue(
            self.container.add_item(self.item_b, Position(3, 0, 0), 2, 2, 2)
        )

        self.assertEqual(len(self.container.packed_items), 2)
        self.assertEqual(self.container.packed_weight, 15.0)


if __name__ == "__main__":
    unittest.main()
