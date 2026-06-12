import json
from typing import Tuple, List, Dict, Any, Optional


class Position:
    """Represents a 3D coordinate (x, y, z) in space."""

    __slots__ = ("x", "y", "z")

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)

    def __repr__(self) -> str:
        return f"Position(x={self.x}, y={self.y}, z={self.z})"


class Item:
    """Represents a 3D box with initial dimensions (width, height, depth) and weight."""

    __slots__ = (
        "name",
        "width",
        "height",
        "depth",
        "weight",
        "_volume",
        "_orientations",
    )

    def __init__(
        self, name: str, width: float, height: float, depth: float, weight: float = 0.0
    ):
        assert width > 0 and height > 0 and depth > 0, "Dimensions must be positive"
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.weight = weight
        self._volume = width * height * depth

        dims = [width, height, depth]
        orientations = []
        import itertools

        for p in itertools.permutations(dims):
            if p not in orientations:
                orientations.append(p)
        self._orientations = orientations

    @property
    def volume(self) -> float:
        return self._volume

    def get_all_orientations(self) -> List[Tuple[float, float, float]]:
        """Returns precomputed list of unique (width, height, depth) orientations."""
        return self._orientations

    def __repr__(self) -> str:
        return f"Item(name='{self.name}', dims=({self.width}x{self.height}x{self.depth}), weight={self.weight})"


class PackedItem:
    """Represents an item that is placed in a container at a specific position and orientation."""

    __slots__ = (
        "item",
        "x",
        "y",
        "z",
        "width",
        "height",
        "depth",
        "max_x",
        "max_y",
        "max_z",
    )

    def __init__(
        self, item: Item, position: Position, width: float, height: float, depth: float
    ):
        self.item = item
        self.x = position.x
        self.y = position.y
        self.z = position.z
        self.width = width
        self.height = height
        self.depth = depth

        self.max_x = self.x + width
        self.max_y = self.y + height
        self.max_z = self.z + depth

    def intersects(self, other: "PackedItem") -> bool:
        """High-performance AABB overlap check using precomputed direct values."""
        return (
            self.x < other.max_x
            and self.max_x > other.x
            and self.y < other.max_y
            and self.max_y > other.y
            and self.z < other.max_z
            and self.max_z > other.z
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the packed item for visualizer output."""
        return {
            "name": self.item.name,
            "position": {"x": self.x, "y": self.y, "z": self.z},
            "dimensions": {"w": self.width, "h": self.height, "d": self.depth},
            "weight": self.item.weight,
        }

    def __repr__(self) -> str:
        return f"PackedItem({self.item.name} at ({self.x},{self.y},{self.z}) dims=({self.width}x{self.height}x{self.depth}))"


class Container:
    """Represents the container/bin where items are packed."""

    def __init__(
        self,
        width: float,
        height: float,
        depth: float,
        max_weight: float = float("inf"),
    ):
        self.width = width
        self.height = height
        self.depth = depth
        self.max_weight = max_weight
        self.packed_items: List[PackedItem] = []
        self._packed_weight = 0.0
        self._packed_volume = 0.0

    @property
    def volume(self) -> float:
        return self.width * self.height * self.depth

    @property
    def packed_volume(self) -> float:
        return self._packed_volume

    @property
    def packed_weight(self) -> float:
        return self._packed_weight

    @property
    def efficiency(self) -> float:
        """Returns the volume utilization efficiency as a percentage (0-100)."""
        vol = self.volume
        if vol == 0:
            return 0.0
        return (self._packed_volume / vol) * 100.0

    def fits_inside(self, position: Position, w: float, h: float, d: float) -> bool:
        """Checks if a box with dimensions (w, h, d) at position fits fully inside the container boundaries."""
        return (
            position.x >= 0
            and position.x + w <= self.width
            and position.y >= 0
            and position.y + h <= self.height
            and position.z >= 0
            and position.z + d <= self.depth
        )

    def check_collision(self, test_item: PackedItem) -> bool:
        """Checks if the test_item overlaps with any already packed items in the container."""
        tx1, tx2 = test_item.x, test_item.max_x
        ty1, ty2 = test_item.y, test_item.max_y
        tz1, tz2 = test_item.z, test_item.max_z

        for pi in self.packed_items:
            if (
                tx1 < pi.max_x
                and tx2 > pi.x
                and ty1 < pi.max_y
                and ty2 > pi.y
                and tz1 < pi.max_z
                and tz2 > pi.z
            ):
                return True
        return False

    def add_item(
        self, item: Item, position: Position, w: float, h: float, d: float
    ) -> bool:
        """Attempts to add an item to the container. Returns True if successful."""
        test_item = PackedItem(item, position, w, h, d)

        if not self.fits_inside(position, w, h, d):
            return False

        if self._packed_weight + item.weight > self.max_weight:
            return False

        if self.check_collision(test_item):
            return False

        self.packed_items.append(test_item)
        self._packed_weight += item.weight
        self._packed_volume += w * h * d
        return True

    def clear(self):
        """Clears all packed items from the container."""
        self.packed_items.clear()
        self._packed_weight = 0.0
        self._packed_volume = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the container and its contents."""
        return {
            "container_dimensions": {
                "W": self.width,
                "H": self.height,
                "D": self.depth,
            },
            "max_weight": self.max_weight if self.max_weight != float("inf") else None,
            "packed_volume_percentage": self.efficiency,
            "total_items": len(self.packed_items),
            "packed_items": [item.to_dict() for item in self.packed_items],
        }
