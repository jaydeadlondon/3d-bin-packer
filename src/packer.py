from typing import List, Tuple, Optional, Set
from src.geometry import Position, Item, PackedItem, Container


class Packer:
    """Performs 3D bin packing using the Extreme Points (EP) heuristic and support verification."""

    def __init__(self, container: Container, stability_threshold: float = 0.5):
        """
        :param container: The Container to pack items into.
        :param stability_threshold: Fraction of bottom face area (0.0 to 1.0)
                                     that must be supported by either the container floor (z=0)
                                     or upper faces of other packed items.
        """
        self.container = container
        self.stability_threshold = stability_threshold
        self.extreme_points: List[Tuple[float, float, float]] = [(0.0, 0.0, 0.0)]

    def reset(self):
        """Resets the packer state and container."""
        self.container.clear()
        self.extreme_points = [(0.0, 0.0, 0.0)]

    def is_supported(self, x: float, y: float, z: float, w: float, h: float) -> bool:
        """
        Checks if a box with dimensions w x h placed at (x, y, z) is physically stable.
        """
        if z == 0.0:
            return True

        target_area = w * h
        supported_area = 0.0

        eps = 1e-5
        bottom_x1, bottom_x2 = x, x + w
        bottom_y1, bottom_y2 = y, y + h

        for item in self.container.packed_items:
            if abs(item.max_z - z) < eps:
                overlap_x1 = max(bottom_x1, item.x)
                overlap_x2 = min(bottom_x2, item.max_x)
                overlap_y1 = max(bottom_y1, item.y)
                overlap_y2 = min(bottom_y2, item.max_y)

                if overlap_x2 > overlap_x1 and overlap_y2 > overlap_y1:
                    supported_area += (overlap_x2 - overlap_x1) * (
                        overlap_y2 - overlap_y1
                    )
                    if (supported_area / target_area) >= self.stability_threshold:
                        return True

        return (supported_area / target_area) >= self.stability_threshold

    def _update_extreme_points(self, new_packed_item: PackedItem):
        """
        Generates new extreme points and prunes invalid ones.
        Uses optimized tuples and fast filters.
        """
        x, y, z = new_packed_item.x, new_packed_item.y, new_packed_item.z
        w, h, d = new_packed_item.width, new_packed_item.height, new_packed_item.depth

        max_x, max_y, max_z = x + w, y + h, z + d

        candidates = [(max_x, y, z), (x, max_y, z), (x, y, max_z)]

        eps = 1e-5
        cw, ch, cd = self.container.width, self.container.height, self.container.depth

        valid_points = []
        for ep_x, ep_y, ep_z in self.extreme_points:
            inside = (
                x - eps < ep_x < max_x - eps
                and y - eps < ep_y < max_y - eps
                and z - eps < ep_z < max_z - eps
            )
            if not inside:
                valid_points.append((ep_x, ep_y, ep_z))

        packed_coords = [
            (pi.x, pi.max_x, pi.y, pi.max_y, pi.z, pi.max_z)
            for pi in self.container.packed_items
        ]

        for cx, cy, cz in candidates:
            if cx < cw and cy < ch and cz < cd:
                covered = False
                for px, pmax_x, py, pmax_y, pz, pmax_z in packed_coords:
                    if (
                        px - eps < cx < pmax_x - eps
                        and py - eps < cy < pmax_y - eps
                        and pz - eps < cz < pmax_z - eps
                    ):
                        covered = True
                        break
                if not covered:
                    valid_points.append((cx, cy, cz))

        unique_points = []
        for p in valid_points:
            is_dup = False
            for u in unique_points:
                if (
                    abs(p[0] - u[0]) < eps
                    and abs(p[1] - u[1]) < eps
                    and abs(p[2] - u[2]) < eps
                ):
                    is_dup = True
                    break
            if not is_dup:
                unique_points.append(p)

        self.extreme_points = unique_points

    def find_best_placement(
        self, item: Item
    ) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        """
        Finds the best extreme point and orientation for the given item.
        We rank placements based on a heuristic score:
        - Primary: Min Z (packing as low as possible).
        - Secondary: Min Y (packing as deep as possible).
        - Tertiary: Min X (packing as left as possible).
        """
        best_ep = None
        best_orientation = None
        best_score = float("inf")

        orientations = item.get_all_orientations()

        sorted_eps = sorted(self.extreme_points, key=lambda ep: (ep[2], ep[1], ep[0]))

        container = self.container
        has_stability = self.stability_threshold > 0

        for ep_x, ep_y, ep_z in sorted_eps:
            if ep_z * 1000 >= best_score:
                break

            for w, h, d in orientations:
                if (
                    ep_x + w > container.width
                    or ep_y + h > container.height
                    or ep_z + d > container.depth
                ):
                    continue

                test_item = PackedItem(item, Position(ep_x, ep_y, ep_z), w, h, d)
                if container.check_collision(test_item):
                    continue

                if has_stability:
                    if not self.is_supported(ep_x, ep_y, ep_z, w, h):
                        continue

                score = ep_z * 1000 + ep_y * 10 + ep_x

                if score < best_score:
                    best_score = score
                    best_ep = (ep_x, ep_y, ep_z)
                    best_orientation = (w, h, d)

        if best_ep and best_orientation:
            return best_ep, best_orientation
        return None

    def pack(self, items: List[Item], sort_strategy: str = "volume_desc") -> List[Item]:
        """
        Packs a list of items into the container.
        """
        if sort_strategy == "volume_desc":
            sorted_items = sorted(items, key=lambda it: it._volume, reverse=True)
        elif sort_strategy == "area_desc":
            sorted_items = sorted(
                items, key=lambda it: it.width * it.height, reverse=True
            )
        elif sort_strategy == "max_dim_desc":
            sorted_items = sorted(
                items, key=lambda it: max(it.width, it.height, it.depth), reverse=True
            )
        elif sort_strategy == "weight_desc":
            sorted_items = sorted(items, key=lambda it: it.weight, reverse=True)
        else:
            sorted_items = items[:]

        unpacked_items = []

        find_best = self.find_best_placement
        add_item = self.container.add_item
        update_eps = self._update_extreme_points

        for item in sorted_items:
            placement = find_best(item)
            if placement:
                (ep_x, ep_y, ep_z), (w, h, d) = placement
                success = add_item(item, Position(ep_x, ep_y, ep_z), w, h, d)
                if success:
                    update_eps(self.container.packed_items[-1])
                else:
                    unpacked_items.append(item)
            else:
                unpacked_items.append(item)

        return unpacked_items
