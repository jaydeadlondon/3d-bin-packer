import unittest
from src.geometry import Position, Item, Container
from src.packer import Packer


class TestPacker(unittest.TestCase):
    def setUp(self):
        self.container = Container(10, 10, 10, max_weight=500)
        self.packer = Packer(self.container, stability_threshold=0.5)

    def test_basic_packing(self):
        items = [
            Item("Box1", 5, 5, 2),
            Item("Box2", 5, 5, 2),
        ]
        unpacked = self.packer.pack(items, sort_strategy="volume_desc")
        self.assertEqual(len(unpacked), 0)
        self.assertEqual(len(self.container.packed_items), 2)

        self.assertAlmostEqual(self.container.efficiency, 10.0)

    def test_stability_check(self):
        box_floor = Item("FloorBox", 4, 4, 2)
        self.packer.pack([box_floor])

        box_top = Item("TopBox", 4, 4, 2)
        unpacked = self.packer.pack([box_top])
        self.assertEqual(len(unpacked), 0)
        self.assertEqual(len(self.container.packed_items), 2)

        self.packer.reset()
        pillar = Item("Pillar", 2, 2, 2)
        huge = Item("Huge", 6, 6, 2)

        self.packer.pack([pillar])

        small_container = Container(6, 6, 4)
        strict_packer = Packer(small_container, stability_threshold=0.5)

        unpacked_strict = strict_packer.pack([pillar, huge], sort_strategy="none")
        self.assertEqual(len(unpacked_strict), 1)
        self.assertEqual(unpacked_strict[0].name, "Huge")


if __name__ == "__main__":
    unittest.main()
