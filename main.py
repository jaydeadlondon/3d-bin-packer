import argparse
import json
import random
import os
from typing import List
from src.geometry import Container, Item
from src.packer import Packer


def generate_items_dataset(count: int, seed: int) -> List[Item]:
    """Generates a reproducible randomized dataset of 3D boxes."""
    if seed is not None:
        random.seed(seed)

    items = []
    profiles = [
        {
            "w_min": 1,
            "w_max": 3,
            "h_min": 1,
            "h_max": 3,
            "d_min": 1,
            "d_max": 3,
            "w_coef": 2,
        },
        {
            "w_min": 2,
            "w_max": 5,
            "h_min": 2,
            "h_max": 4,
            "d_min": 1,
            "d_max": 3,
            "w_coef": 5,
        },
        {
            "w_min": 3,
            "w_max": 6,
            "h_min": 2,
            "h_max": 5,
            "d_min": 2,
            "d_max": 4,
            "w_coef": 10,
        },
    ]

    for i in range(count):
        prof = random.choice(profiles)
        w = random.randint(prof["w_min"], prof["w_max"])
        h = random.randint(prof["h_min"], prof["h_max"])
        d = random.randint(prof["d_min"], prof["d_max"])

        volume = w * h * d
        weight = volume * prof["w_coef"] * random.uniform(0.8, 1.2)

        items.append(Item(f"Box_{i+1:03d}", w, h, d, round(weight, 1)))

    return items


def main():
    parser = argparse.ArgumentParser(
        description="3D Bin Packing Optimizer & Isometric Report Generator."
    )

    parser.add_argument(
        "--width", type=float, default=15.0, help="Container width (X-axis)"
    )
    parser.add_argument(
        "--height", type=float, default=15.0, help="Container height (Y-axis)"
    )
    parser.add_argument(
        "--depth", type=float, default=15.0, help="Container depth (Z-axis)"
    )
    parser.add_argument(
        "--max-weight",
        type=float,
        default=10000.0,
        help="Container maximum weight capacity",
    )

    parser.add_argument(
        "--items", type=int, default=80, help="Number of random items to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=100,
        help="Random seed for item dimensions generator",
    )

    parser.add_argument(
        "--strategy",
        type=str,
        default="volume_desc",
        choices=["volume_desc", "area_desc", "max_dim_desc", "weight_desc", "none"],
        help="Heuristic sorting strategy before packing",
    )
    parser.add_argument(
        "--stability",
        type=float,
        default=0.5,
        help="Gravity stability support threshold (0.0 to 1.0, e.g. 0.5 = 50% bottom area supported)",
    )

    parser.add_argument(
        "--out",
        type=str,
        default="result.html",
        help="Output interactive HTML visualizer file",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("      📦 3D BIN PACKING OPTIMIZER & REPORT GENERATOR 📦")
    print("=" * 60)
    print(
        f"Container configuration: {args.width}x{args.height}x{args.depth}, Max Weight: {args.max_weight} kg"
    )
    print(f"Generating {args.items} random items (Seed: {args.seed})...")

    items = generate_items_dataset(args.items, args.seed)
    total_items_volume = sum(item.volume for item in items)
    print(f"Total volume of generated items: {total_items_volume:.1f} m³")
    container = Container(args.width, args.height, args.depth, args.max_weight)
    packer = Packer(container, stability_threshold=args.stability)

    print(
        f"Packing items using '{args.strategy}' strategy (Stability check: {args.stability * 100:.0f}%)..."
    )

    import time

    start_t = time.perf_counter()
    unpacked_items = packer.pack(items, sort_strategy=args.strategy)
    end_t = time.perf_counter()

    elapsed = end_t - start_t

    packed_count = len(container.packed_items)
    unpacked_count = len(unpacked_items)
    utilization = container.efficiency

    print("-" * 60)
    print(f"Packing completed in {elapsed:.4f} seconds!")
    print(
        f"Successfully packed : {packed_count} / {args.items} items ({packed_count/args.items*100:.1f}%)"
    )
    print(f"Could not pack      : {unpacked_count} items")
    print(f"Container utilization: {utilization:.2f}%")
    print(
        f"Total packed weight : {container.packed_weight:.1f} / {container.max_weight:.1f} kg"
    )
    print("-" * 60)

    packing_results = container.to_dict()
    packing_results["unpacked_items"] = [
        {
            "name": it.name,
            "dimensions": {"w": it.width, "h": it.height, "d": it.depth},
            "weight": it.weight,
        }
        for it in unpacked_items
    ]

    template_path = os.path.join("src", "visualizer.html")
    if not os.path.exists(template_path):
        print(f"Error: Base visualizer template '{template_path}' not found!")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    json_data_str = json.dumps(packing_results, indent=4, ensure_ascii=False)
    injection_code = f"packingData = {json_data_str};"

    html_with_data = html_content.replace(
        "/*INJECTED_DATA_PLACEHOLDER*/", injection_code
    )

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_with_data)

    print(f"Success! Interactive visualizer saved to: {args.out}")
    print(
        "You can now open it in the preview or any web browser to see the 3D packing."
    )
    print("=" * 60)


if __name__ == "__main__":
    main()
