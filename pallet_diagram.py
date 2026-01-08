"""
Generate two diagrams:

1) pallet_diagram.png
   Shows a single pallet (LxWxH) with item/case cubes packed on it.

2) location_diagram.png
   Shows multiple pallets stacked in a row using the provided stack counts.

Run:
    python pallet_diagram.py

Requires: matplotlib (install with: pip install matplotlib)
"""
from __future__ import annotations

import math
import numpy as np
from pathlib import Path
from time import sleep

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Configurable parameters
# 2*4*3
PALLET_DIMS = (2.0, 1.0, 0.8)     # pallet (length, width, height) in meters
ITEM_DIMS = (0.25, 1.0, 0.25)    # item/case size in meters (cube)
STACK_MAX = 2                    # maximum allowed pallet stack height
AISLE_GAP = 0.2                 # gap between pallet positions (meters)
# LOCATION_DIMS = (18.0, 6.0, 4.0)  # location footprint (length, width, height) in meters
LOCATION_DIMS = (8, 1.2, 2.0)  # location footprint (length, width, height) in meters
PALLET_OUTPUT = Path("pallet_diagram.png")
LOCATION_OUTPUT = Path("location_diagram.png")


def _cuboid_vertices(origin: tuple[float, float, float], size: tuple[float, float, float]):
    """Return list of vertices for a cuboid starting at origin with given size."""
    ox, oy, oz = origin
    lx, ly, lz = size
    return [
        (ox, oy, oz),
        (ox + lx, oy, oz),
        (ox + lx, oy + ly, oz),
        (ox, oy + ly, oz),
        (ox, oy, oz + lz),
        (ox + lx, oy, oz + lz),
        (ox + lx, oy + ly, oz + lz),
        (ox, oy + ly, oz + lz),
    ]


def visualize_poly3d_collection(collection_object):
    """
    Creates a figure and displays the Poly3DCollection object.

    Args:
        collection_object (Poly3DCollection): The object to visualize.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    # Add the collection to the axes
    ax.add_collection3d(collection_object)

    # Optional: Set limits automatically based on the collection's vertices
    # This part might need adjustment depending on your specific data structure
    # For a general approach, you might need to manually set limits
    try:
        # Get all vertices from the collection
        all_verts = np.vstack([p.vertices for p in collection_object.get_paths()])
        if len(all_verts) > 0:
            ax.set_xlim([all_verts[:, 0].min(), all_verts[:, 0].max()])
            ax.set_ylim([all_verts[:, 1].min(), all_verts[:, 1].max()])
            ax.set_zlim([all_verts[:, 2].min(), all_verts[:, 2].max()])
    except Exception as e:
        print(f"Could not automatically set axes limits: {e}")
        # Fallback to manual limits if automatic fails
        ax.set_xlim([-1, 1])
        ax.set_ylim([-1, 1])
        ax.set_zlim([-1, 1])

    ax.set_xlabel("X axis")
    ax.set_ylabel("Y axis")
    ax.set_zlabel("Z axis")

    # Display the plot
    plt.show()


def _add_cuboid(ax, origin, size, color, zorder = 999):
    """Draw a single cuboid (pallet or item)."""
    v = _cuboid_vertices(origin, size)
    faces = [
        [v[0], v[1], v[2], v[3]],  # bottom
        [v[4], v[5], v[6], v[7]],  # top
        [v[0], v[1], v[5], v[4]],
        [v[1], v[2], v[6], v[5]],
        [v[2], v[3], v[7], v[6]],
        [v[3], v[0], v[4], v[7]],
    ]
    poly = Poly3DCollection(faces, alpha=0.9, facecolors=color, edgecolors="black", linewidths=0.6, zorder=zorder)
    # poly.set_zsort('min')
    ax.add_collection3d(poly)


def draw_pallet_diagram(
    pallet_dims: tuple[float, float, float] = PALLET_DIMS,
    item_dims: tuple[float, float, float] = ITEM_DIMS,
    output_path: Path | str = PALLET_OUTPUT,
) -> Path:
    """Render a single pallet loaded with item cubes and save it as PNG."""
    p_len, p_wid, p_hgt = pallet_dims
    i_len, i_wid, i_hgt = item_dims

    base_thickness = max(i_hgt * 0.2, 0.03)
    usable_height = max(i_hgt, p_hgt - base_thickness)

    count_x = max(1, int(p_len // i_len))
    count_y = max(1, int(p_wid // i_wid))
    count_z = max(1, int(usable_height // i_hgt))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.computed_zorder = False

    # Draw pallet base
    _add_cuboid(ax, (0.0, 0.0, 0.0), (p_len, p_wid, base_thickness), (0.7, 0.5, 0.3), zorder=0)
    

    # Draw items stacked on pallet
    i = 0
    for iz in range(count_z):
        # Linearly shrink columns with height to form a triangular profile
        cols_this_layer = count_x if count_z == 1 else max(1, count_x - math.floor((count_x - 1) * iz / (count_z - 1)))
        for ix in range(cols_this_layer):
            for iy in range(count_y):
                origin = (ix * i_len, iy * i_wid, base_thickness + iz * i_hgt)
                shade = 0.35 + 0.12 * (iz / max(1, count_z - 1))
                color = (0.25, 0.6 + shade * 0.3, 0.25)
                i += 1
                _add_cuboid(ax, origin, (i_len, i_wid, i_hgt), color, zorder=100 + ix - iy + iz)

    total_len = count_x * i_len
    total_wid = count_y * i_wid
    total_hgt = base_thickness + count_z * i_hgt

    ax.set_xlim(0, total_len)
    ax.set_ylim(0, total_wid)
    ax.set_zlim(0, total_hgt * 1.2)

    ax.set_xlabel(f"Length (m): {count_x} items")
    ax.set_ylabel(f"Width (m): {count_y} items")
    ax.set_zlabel(f"Height (m): {count_z} items")

    fig.suptitle("Pallet Diagram", fontsize=14, fontweight='bold')

    ax.view_init(elev=22, azim=-50)
    ax.grid(False)
    ax.set_box_aspect((total_len, total_wid, total_hgt))

    plt.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def draw_location_diagram(
    pallet_dims: tuple[float, float, float] = PALLET_DIMS,
    max_stack_allowed: int = STACK_MAX,
    aisle_gap: float = AISLE_GAP,
    location_dims: tuple[float, float, float] = LOCATION_DIMS,
    output_path: Path | str = LOCATION_OUTPUT,
) -> Path:
    """Render pallets in a 2D grid within the given location footprint and save as PNG."""
    length, width, height = pallet_dims
    location_len, location_wid, location_hgt = location_dims

    # Compute how many pallet slots fit when rotated 90° (swap length/width axes)
    slot_x = width + aisle_gap   # pallets laid along original width on X
    slot_y = length + aisle_gap  # pallets laid along original length on Y
    slots_x = max(1, int(location_wid // slot_x))
    slots_y = max(1, int(location_len // slot_y))
    max_stack_cap = max(1, int(location_hgt // height))
    max_layers = max(1, min(max_stack_cap, max_stack_allowed))

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection="3d")

    max_stack_used = 0
    for level in range(max_layers):
        cols_this_layer = slots_x if max_layers == 1 else max(1, slots_x - math.floor((slots_x - 1) * level / (max_layers - 1)))
        for iy in range(slots_y):
            for ix in range(cols_this_layer):
                max_stack_used = max(max_stack_used, level + 1)
                origin = (ix * slot_x, iy * slot_y, level * height)
                shade = 0.6 + 0.1 * (level / max(1, max_layers - 1))
                color = (0.3, shade, 0.3)
                # remove the last _cuboid_vertices
                if level == max_layers - 1 and ix == cols_this_layer - 1 and iy == 0:
                    # Topmost pallet at the far corner is semi-transparent to show location limits
                    color = (0.8, 0.2, 0.2, 0.3)
                    # continue
                _add_cuboid(ax, origin, (width, length, height), color, zorder=100 + ix - iy + level)

    # Axes limits respect the location footprint
    ax.set_xlim(0, location_wid)
    ax.set_ylim(0, location_len)
    ax.set_zlim(0, location_hgt)

    ax.set_xlabel(f"Width (m): {slots_x} pallets across")
    ax.set_ylabel(f"Length (m): {slots_y} pallets across")
    ax.set_zlabel(f"Height (m): up to {max_layers} pallets")

    fig.suptitle("Location Diagram", fontsize=14, fontweight='bold')

    ax.view_init(elev=20, azim=-60)
    ax.grid(False)
    ax.set_box_aspect((location_wid, location_len, location_hgt))
    plt.tight_layout()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main():
    pallet_path = draw_pallet_diagram()
    print(f"Saved pallet diagram to {pallet_path.resolve()}")

    location_path = draw_location_diagram()
    print(f"Saved location diagram to {location_path.resolve()}")


if __name__ == "__main__":
    main()
