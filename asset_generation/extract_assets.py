#!/usr/bin/env python3
"""
Extract images from composite images in chatgpt_assets/new folder.
Each image contains multiple white-framed portraits on a black background.
Finds connected non-black regions (portraits) and extracts them, trimming white frames.
"""

import argparse
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage

# Character names in order (left to right, top to bottom)
CHARACTER_NAMES = ["Alice", "Bob", "Charlie", "Doris", "Edith", "Frank"]

# Paths
ASSETS_DIR = Path(__file__).parent / "images"
OUTPUT_DIR = Path(__file__).parent / "outputs"

# Threshold for detecting black background (0-255)
BLACK_THRESHOLD = 30
# Threshold for detecting white borders to trim (0-255)
# Lower value = more aggressive trimming of light-colored borders
WHITE_THRESHOLD = 150
# Fixed margin to trim from each edge (in pixels) - for decorative borders
TRIM_MARGIN = 12
# Minimum area for a valid portrait region (to filter noise)
MIN_REGION_AREA = 5000


def find_portrait_regions(img_array):
    """
    Find portrait regions by detecting connected non-black areas.
    Returns list of bounding boxes (left, top, right, bottom) sorted by position.
    """
    height, width = img_array.shape[:2]

    # Convert to grayscale
    if len(img_array.shape) == 3:
        gray = np.mean(img_array[:, :, :3], axis=2)
    else:
        gray = img_array.astype(float)

    # Create binary mask: non-black pixels = True (portraits + frames)
    non_black_mask = gray > BLACK_THRESHOLD

    # Label connected components
    labeled_array, num_features = ndimage.label(non_black_mask)

    # Get bounding boxes and areas for each region
    regions = []
    for label_id in range(1, num_features + 1):
        # Find all pixels with this label
        ys, xs = np.where(labeled_array == label_id)

        if len(ys) == 0:
            continue

        # Calculate bounding box
        min_y, max_y = ys.min(), ys.max()
        min_x, max_x = xs.min(), xs.max()

        # Calculate area
        area = len(ys)

        # Filter by minimum area
        if area >= MIN_REGION_AREA:
            regions.append(
                {
                    "bbox": (min_x, min_y, max_x + 1, max_y + 1),
                    "area": area,
                    "center_y": (min_y + max_y) / 2,
                    "center_x": (min_x + max_x) / 2,
                }
            )

    # Select the 6 largest regions (the actual portraits)
    regions.sort(key=lambda r: r["area"], reverse=True)
    top_regions = regions[:6]

    # Now sort these 6 by position: top to bottom, then left to right
    if top_regions:
        # Determine row threshold (half the average height)
        avg_height = np.mean([(r["bbox"][3] - r["bbox"][1]) for r in top_regions])
        row_threshold = avg_height / 2

        # Sort: group by rows first, then by x position within each row
        top_regions.sort(
            key=lambda r: (
                int(r["center_y"] / row_threshold),  # Row grouping
                r["center_x"],  # Left to right within row
            )
        )

    return [r["bbox"] for r in top_regions]


def trim_white_border(img):
    """
    Trim borders from an image.
    First applies a fixed margin trim, then finds bounding box of non-white pixels.
    """
    img_array = np.array(img)
    height, width = img_array.shape[:2]

    if height == 0 or width == 0:
        return img

    # First, apply fixed margin trim to remove decorative borders
    margin = TRIM_MARGIN
    if height > margin * 2 and width > margin * 2:
        img = img.crop((margin, margin, width - margin, height - margin))
        img_array = np.array(img)
        height, width = img_array.shape[:2]

    # Convert to grayscale for analysis
    if len(img_array.shape) == 3:
        gray = np.mean(img_array[:, :, :3], axis=2)
    else:
        gray = img_array.astype(float)

    # Find all non-white pixels (content)
    non_white_mask = gray < WHITE_THRESHOLD

    # Find bounding box of non-white pixels
    rows_with_content = np.any(non_white_mask, axis=1)
    cols_with_content = np.any(non_white_mask, axis=0)

    if not np.any(rows_with_content) or not np.any(cols_with_content):
        return img  # All white or empty, return as-is

    # Find first and last rows/cols with content
    row_indices = np.where(rows_with_content)[0]
    col_indices = np.where(cols_with_content)[0]

    top = row_indices[0]
    bottom = row_indices[-1] + 1
    left = col_indices[0]
    right = col_indices[-1] + 1

    # Crop if valid
    if top < bottom and left < right:
        return img.crop((left, top, right, bottom))
    return img


def extract_portraits(image_path, output_dir, scale=1.0):
    """
    Extract portrait images from a composite image.
    Finds non-black regions and extracts them, trimming white borders.

    Args:
        image_path: Path to the composite image
        output_dir: Directory to save extracted portraits
        scale: Scale factor for output images (e.g., 0.5 for 50% size)
    """
    print(f"Processing {image_path.name}...")

    # Load image
    img = Image.open(image_path)
    img_array = np.array(img)
    height, width = img_array.shape[:2]

    print(f"  Image size: {width}x{height}px")

    # Find portrait regions
    regions = find_portrait_regions(img_array)

    print(f"  Found {len(regions)} portrait region(s) (using 6 largest)")

    # Extract and process each portrait
    extracted = []
    for i, (left, top, right, bottom) in enumerate(regions[:6]):
        # Extract region
        region = img.crop((left, top, right, bottom))

        # Trim white border
        trimmed = trim_white_border(region)

        # Convert to RGB if needed
        if trimmed.mode in ("RGBA", "LA", "P"):
            rgb_img = Image.new("RGB", trimmed.size, (0, 0, 0))
            if trimmed.mode == "P":
                trimmed = trimmed.convert("RGBA")
            if trimmed.mode in ("RGBA", "LA"):
                rgb_img.paste(trimmed, mask=trimmed.split()[-1])
            else:
                rgb_img.paste(trimmed)
            trimmed = rgb_img
        elif trimmed.mode != "RGB":
            trimmed = trimmed.convert("RGB")

        if trimmed.size[0] > 0 and trimmed.size[1] > 0:
            extracted.append(trimmed)
            print(
                f"    Region {i + 1}: {right - left}x{bottom - top} -> {trimmed.size[0]}x{trimmed.size[1]} (trimmed)"
            )
        else:
            print(f"    Region {i + 1}: Empty after trimming, skipping")

    # Save with character names
    base_name = image_path.stem
    for portrait, char_name in zip(extracted[:6], CHARACTER_NAMES):
        # Apply scaling if needed
        if scale != 1.0:
            new_width = int(portrait.size[0] * scale)
            new_height = int(portrait.size[1] * scale)
            portrait = portrait.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )

        output_path = output_dir / f"{char_name}_{base_name}.jpg"
        portrait.save(output_path, "JPEG", quality=95)
        print(f"  Saved {output_path.name} ({portrait.size[0]}x{portrait.size[1]})")

    return len(extracted)


def main():
    """Main function to process all images."""
    parser = argparse.ArgumentParser(
        description="Extract portrait images from composite images."
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale factor for output images (e.g., 0.5 for 50%% size). Default: 1.0",
    )
    args = parser.parse_args()

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Check if assets directory exists
    if not ASSETS_DIR.exists():
        print(f"Error: Assets directory not found: {ASSETS_DIR}")
        return

    # Get all PNG files
    image_files = list(ASSETS_DIR.glob("*.png"))

    if not image_files:
        print(f"No PNG files found in {ASSETS_DIR}")
        return

    print(f"Found {len(image_files)} image(s) to process")
    if args.scale != 1.0:
        print(f"Output scale: {args.scale * 100:.0f}%")
    print()

    # Process each image
    total_extracted = 0
    for image_path in sorted(image_files):
        try:
            count = extract_portraits(image_path, OUTPUT_DIR, scale=args.scale)
            total_extracted += count
            print()
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}\n")
            import traceback

            traceback.print_exc()

    print(f"Done! Extracted {total_extracted} portraits total.")


if __name__ == "__main__":
    main()
