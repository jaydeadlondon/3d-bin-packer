import time
import random
import cProfile
import pstats
from typing import List
from src.geometry import Container, Item
from src.packer import Packer


def generate_random_items(count: int, seed: int = 42) -> List[Item]:
    """Generates a list of random items for stress testing."""
    random.seed(seed)
    items = []
    for i in range(count):
        w = random.randint(1, 4)
        h = random.randint(1, 4)
        d = random.randint(1, 4)
        weight = random.uniform(1.0, 10.0)
        items.append(Item(f"Box_{i}", w, h, d, weight))
    return items


def run_benchmark(item_count: int, stability: float = 0.5):
    container = Container(width=30, height=30, depth=30, max_weight=100000.0)
    packer = Packer(container, stability_threshold=stability)

    items = generate_random_items(item_count)

    start_time = time.perf_counter()
    unpacked = packer.pack(items, sort_strategy="volume_desc")
    end_time = time.perf_counter()

    duration = end_time - start_time
    packed_count = len(container.packed_items)
    unpacked_count = len(unpacked)
    efficiency = container.efficiency

    print(f"--- Benchmark Results ({item_count} items, stability={stability}) ---")
    print(f"Execution time  : {duration:.4f} seconds")
    print(
        f"Packed items    : {packed_count}/{item_count} ({packed_count/item_count*100:.1f}%)"
    )
    print(f"Unpacked items  : {unpacked_count}")
    print(f"Container efficiency: {efficiency:.2f}%")
    print(f"Extreme points left : {len(packer.extreme_points)}")
    print("-" * 50)
    return duration


def profile_packer():
    print("Running Profiler on packing 500 items...")
    container = Container(width=30, height=30, depth=30)
    packer = Packer(container, stability_threshold=0.5)
    items = generate_random_items(500)

    profiler = cProfile.Profile()
    profiler.enable()
    packer.pack(items, sort_strategy="volume_desc")
    profiler.disable()

    stats = pstats.Stats(profiler).sort_stats("cumulative")
    stats.print_stats(15)


if __name__ == "__main__":
    run_benchmark(100)
    run_benchmark(300)
    run_benchmark(600)
    profile_packer()
