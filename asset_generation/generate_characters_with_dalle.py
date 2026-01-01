#!/usr/bin/env python3
"""
Generate character images with all poses in a single DALL-E 3 image, then split them.
"""

import argparse
import os
import base64
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from io import BytesIO

import yaml
import numpy as np
from PIL import Image
from openai import OpenAI


def determine_layout(num_poses: int) -> Tuple[int, int]:
    """
    Determine optimal grid layout (rows, cols) for given number of poses.
    Prefers layouts closer to square when possible.
    """
    if num_poses <= 0:
        raise ValueError("Number of poses must be positive")
    
    # Try to find a layout that's as square as possible
    best_layout = None
    min_aspect_diff = float("inf")
    
    # Try different row counts
    for rows in range(1, num_poses + 1):
        cols = math.ceil(num_poses / rows)
        aspect_ratio = max(rows, cols) / min(rows, cols)
        
        # Prefer layouts closer to square (aspect ratio closer to 1.0)
        if aspect_ratio < min_aspect_diff:
            min_aspect_diff = aspect_ratio
            best_layout = (rows, cols)
    
    return best_layout


def parse_ratio(ratio: str) -> Tuple[float, float]:
    """
    Parse aspect ratio string into (width_ratio, height_ratio) tuple.
    
    Args:
        ratio: Aspect ratio string like "1:1", "4:3", "16:9"
    
    Returns:
        Tuple of (width_ratio, height_ratio)
    """
    try:
        parts = ratio.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid ratio format")
        w_ratio, h_ratio = float(parts[0]), float(parts[1])
        return w_ratio, h_ratio
    except (ValueError, IndexError):
        raise ValueError(f"Invalid aspect ratio format: {ratio}. Expected format: W:H (e.g., 1:1)")


def simplify_ratio(w: float, h: float) -> Tuple[int, int]:
    """
    Simplify a ratio to its lowest terms.
    
    Args:
        w: Width ratio
        h: Height ratio
    
    Returns:
        Tuple of (simplified_width, simplified_height)
    """
    # Find GCD
    gcd = math.gcd(int(w), int(h))
    
    # Simplify
    simplified_w = int(w) // gcd
    simplified_h = int(h) // gcd
    
    return simplified_w, simplified_h


def calculate_overall_ratio(
    layout: Tuple[int, int], vignette_ratio: str
) -> Tuple[float, float]:
    """
    Calculate overall image aspect ratio from layout and vignette ratio.
    
    Args:
        layout: Tuple of (rows, cols) for grid layout
        vignette_ratio: Aspect ratio string for individual vignettes (e.g., "1:1", "4:3")
    
    Returns:
        Tuple of (overall_width_ratio, overall_height_ratio)
    """
    rows, cols = layout
    vignette_w, vignette_h = parse_ratio(vignette_ratio)
    
    # Overall ratio = (cols * vignette_width) : (rows * vignette_height)
    overall_w = cols * vignette_w
    overall_h = rows * vignette_h
    
    return overall_w, overall_h


def aspect_ratio_to_size(ratio: str) -> Tuple[int, int]:
    """
    Convert aspect ratio string to DALL-E 3 compatible size tuple.
    
    Args:
        ratio: Aspect ratio string like "1:1", "4:3", "16:9"
    
    Returns:
        Tuple of (width, height)
    """
    w_ratio, h_ratio = parse_ratio(ratio)
    aspect = w_ratio / h_ratio
    
    # DALL-E 3 supported sizes
    valid_sizes = {
        "1024x1024": (1024, 1024),  # 1:1
        "1792x1024": (1792, 1024),  # ~1.75:1 (close to 16:9)
        "1024x1792": (1024, 1792),  # ~1:1.75 (close to 9:16)
    }
    
    # Find closest matching aspect ratio
    best_size = None
    min_diff = float("inf")
    
    for size_str, (width, height) in valid_sizes.items():
        size_aspect = width / height
        diff = abs(aspect - size_aspect)
        if diff < min_diff:
            min_diff = diff
            best_size = (width, height)
    
    return best_size


def build_multi_pose_prompt(
    character: Dict[str, Any],
    poses: List[Dict[str, Any]],
    layout: Tuple[int, int],
    context: List[str],
    vignette_ratio: str,
) -> str:
    """
    Build a prompt for generating all poses in a single grid image.
    
    Args:
        character: Character dictionary with name, description, background
        poses: List of pose dictionaries with name and description
        layout: Tuple of (rows, cols) for grid layout
        context: List of context strings
        vignette_ratio: Aspect ratio string for individual vignettes (e.g., "1:1", "4:3")
    
    Returns:
        Formatted prompt string
    """
    rows, cols = layout
    context_str = " ".join(context)
    
    # Build position descriptions with explicit grid coordinates
    pose_descriptions = []
    for idx, pose in enumerate(poses):
        row = idx // cols
        col = idx % cols
        
        # Use explicit grid position
        pos_name = f"row {row + 1}, column {col + 1}"
        if rows <= 3 and cols <= 3:
            # Use friendly names for small grids
            friendly_names = {
                (0, 0): "top-left",
                (0, 1): "top-center" if cols == 3 else "top-right",
                (0, 2): "top-right",
                (1, 0): "middle-left" if rows == 3 else "bottom-left",
                (1, 1): "center",
                (1, 2): "middle-right" if rows == 3 else "bottom-right",
                (2, 0): "bottom-left",
                (2, 1): "bottom-center" if cols == 3 else "bottom-right",
                (2, 2): "bottom-right",
            }
            pos_name = friendly_names.get((row, col), pos_name)
        
        pose_descriptions.append(
            f"{pos_name} ({row + 1},{col + 1}): {character['name']} in '{pose['name']}' pose - {pose['description']}"
        )
    
    # Build the full prompt with clear structure
    prompt_parts = [
        context_str,
        "",
        f"CHARACTER: {character['name']}",
        f"Description: {character['description']}",
        f"Background: {character['background']}",
        "",
        f"IMAGE LAYOUT REQUIREMENTS:",
        f"- Create exactly a {rows}x{cols} grid ({rows} rows, {cols} columns)",
        f"- Total of {len(poses)} character poses, one per grid cell",
        f"- Each individual vignette/pose MUST have an aspect ratio of exactly {vignette_ratio}",
        f"- The grid cells must be perfectly aligned and evenly spaced",
        "",
        f"BORDER REQUIREMENTS:",
        f"- Each grid cell must be delimited by pure green lines (RGB: 0, 255, 0; hex: #00FF00)",
        f"- Vertical borders between columns: pure green lines",
        f"- Horizontal borders between rows: pure green lines",
        f"- The green lines should be clearly visible, at least 2-3 pixels wide",
        f"- No other green elements should appear in the image (only the borders)",
        "",
        f"POSE SPECIFICATIONS:",
        *[f"  {desc}" for desc in pose_descriptions],
        "",
        f"STYLE REQUIREMENTS:",
        f"- Pixel art style",
        f"- Cartoonish and kid-friendly",
        f"- Each pose should be clearly distinct and recognizable",
        f"- Maintain character consistency across all poses",
    ]
    
    return "\n".join(prompt_parts)


def detect_and_split_subimages(
    image_path: Path, num_poses: int, layout: Tuple[int, int]
) -> List[Image.Image]:
    """
    Split composite image into subimages based on green border detection or grid layout.
    
    First tries to detect pure green (#00FF00) borders to find cell boundaries.
    Falls back to even grid division if green borders are not detected.
    
    Args:
        image_path: Path to composite image
        num_poses: Number of poses expected
        layout: Tuple of (rows, cols) for grid layout
    
    Returns:
        List of PIL Image objects, one for each subimage
    """
    # Load image
    img = Image.open(image_path)
    width, height = img.size
    
    # Convert to numpy array for processing
    img_array = np.array(img)
    
    rows, cols = layout
    
    # Try to detect green borders
    # Pure green is RGB(0, 255, 0)
    green_threshold = 200  # Threshold for green channel
    red_blue_threshold = 50  # Red and blue should be low
    
    # Detect vertical lines (between columns)
    vertical_lines = []
    for x in range(width):
        # Check if this column has significant green
        column = img_array[:, x, :]
        green_mask = (column[:, 1] > green_threshold) & (column[:, 0] < red_blue_threshold) & (column[:, 2] < red_blue_threshold)
        green_ratio = np.sum(green_mask) / height
        if green_ratio > 0.3:  # At least 30% of column is green
            vertical_lines.append(x)
    
    # Detect horizontal lines (between rows)
    horizontal_lines = []
    for y in range(height):
        # Check if this row has significant green
        row = img_array[y, :, :]
        green_mask = (row[:, 1] > green_threshold) & (row[:, 0] < red_blue_threshold) & (row[:, 2] < red_blue_threshold)
        green_ratio = np.sum(green_mask) / width
        if green_ratio > 0.3:  # At least 30% of row is green
            horizontal_lines.append(y)
    
    # If we found green borders, use them
    if len(vertical_lines) >= cols - 1 and len(horizontal_lines) >= rows - 1:
        # Sort and use the strongest lines
        vertical_lines.sort()
        horizontal_lines.sort()
        
        # Take the most evenly spaced lines
        # For cols, we expect cols-1 vertical dividers
        if len(vertical_lines) > cols - 1:
            # Select evenly spaced lines
            step = len(vertical_lines) // (cols - 1)
            vertical_lines = [vertical_lines[i * step] for i in range(cols - 1)]
        
        if len(horizontal_lines) > rows - 1:
            step = len(horizontal_lines) // (rows - 1)
            horizontal_lines = [horizontal_lines[i * step] for i in range(rows - 1)]
        
        # Add boundaries
        v_boundaries = [0] + vertical_lines + [width]
        h_boundaries = [0] + horizontal_lines + [height]
        
        # Ensure we have the right number of boundaries
        if len(v_boundaries) == cols + 1 and len(h_boundaries) == rows + 1:
            subimages = []
            for row in range(rows):
                for col in range(cols):
                    idx = row * cols + col
                    if idx >= num_poses:
                        break
                    
                    left = v_boundaries[col]
                    top = h_boundaries[row]
                    right = v_boundaries[col + 1]
                    bottom = h_boundaries[row + 1]
                    
                    # Crop, excluding the green borders
                    subimg = img.crop((left, top, right, bottom))
                    subimages.append(subimg)
            
            if len(subimages) == num_poses:
                return subimages
    
    # Fallback to grid-based splitting
    cell_h = height // rows
    cell_w = width // cols
    
    subimages = []
    for row in range(rows):
        for col in range(cols):
            idx = row * cols + col
            if idx >= num_poses:
                break
            
            # Calculate crop box
            left = col * cell_w
            top = row * cell_h
            right = (col + 1) * cell_w if col < cols - 1 else width
            bottom = (row + 1) * cell_h if row < rows - 1 else height
            
            # Crop and add to list
            subimg = img.crop((left, top, right, bottom))
            subimages.append(subimg)
    
    return subimages


def main():
    parser = argparse.ArgumentParser(
        description="Generate character images with all poses in a single DALL-E 3 image"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="character_config.yaml",
        help="Path to character configuration YAML file (default: character_config.yaml)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="all",
        help="Character name to generate, or 'all' for all characters (default: all)",
    )
    parser.add_argument(
        "--ratio",
        type=str,
        default="1:1",
        help="Aspect ratio for individual vignettes/poses like '1:1', '4:3', '16:9' (default: 1:1). The overall image ratio will be calculated from this and the layout.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Output directory for generated images (default: outputs)",
    )
    parser.add_argument(
        "--jpeg",
        action="store_true",
        help="Use JPEG format instead of PNG (default: PNG)",
    )
    parser.add_argument(
        "--quality",
        type=str,
        default="standard",
        choices=["standard", "hd"],
        help="Image quality: 'standard' or 'hd' (default: standard)",
    )
    parser.add_argument(
        "--style",
        type=str,
        default="vivid",
        choices=["vivid", "natural"],
        help="Image style: vivid or natural (default: vivid)",
    )
    parser.add_argument(
        "--save-composite",
        action="store_true",
        help="Save the composite image before splitting (for debugging)",
    )

    args = parser.parse_args()

    # Create backend
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        parser.error("OPENAI_API_KEY environment variable not set")

    backend = OpenAI(api_key=api_key)

    # Validate vignette ratio
    try:
        parse_ratio(args.ratio)
    except ValueError as e:
        parser.error(str(e))

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    context = config.get("context", [])
    characters = config.get("characters", [])

    # Filter characters
    if args.name.lower() != "all":
        characters = [c for c in characters if c["name"].lower() == args.name.lower()]
        if not characters:
            raise ValueError(f"Character '{args.name}' not found in config")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output format
    output_format = "jpeg" if args.jpeg else "png"
    output_ext = "jpg" if args.jpeg else "png"

    # Generate images
    total = 0
    for character in characters:
        poses = character.get("poses", [])
        if not poses:
            print(f"Warning: No poses found for character '{character['name']}'")
            continue

        num_poses = len(poses)
        layout = determine_layout(num_poses)
        
        # Calculate overall aspect ratio from layout and vignette ratio
        overall_w_ratio, overall_h_ratio = calculate_overall_ratio(layout, args.ratio)
        simplified_w, simplified_h = simplify_ratio(overall_w_ratio, overall_h_ratio)
        overall_ratio_str = f"{simplified_w}:{simplified_h}"
        
        # Convert overall ratio to DALL-E compatible size
        try:
            size = aspect_ratio_to_size(overall_ratio_str)
        except ValueError as e:
            print(f"  Error: Could not convert overall ratio {overall_ratio_str} to valid size: {e}")
            continue
        
        print(
            f"Generating {character['name']} with {num_poses} poses in {layout[0]}x{layout[1]} layout..."
        )
        print(f"  Vignette ratio: {args.ratio}, Overall ratio: {overall_ratio_str}")

        # Build prompt
        prompt = build_multi_pose_prompt(character, poses, layout, context, args.ratio)

        # Generate composite image
        try:
            size_str = f"{size[0]}x{size[1]}"
            kwargs_gen = {
                "model": "dall-e-3",
                "prompt": prompt,
                "size": size_str,
                "n": 1,
                "response_format": "b64_json",
                "quality": args.quality,
                "style": args.style,
            }

            # Print generation parameters for debugging
            print(f"  Generation parameters:")
            print(f"    Model: {kwargs_gen['model']}")
            print(f"    Size: {kwargs_gen['size']}")
            print(f"    Quality: {kwargs_gen['quality']}")
            print(f"    Style: {kwargs_gen['style']}")
            print(f"    Layout: {layout[0]}x{layout[1]} grid")
            print(f"    Vignette ratio: {args.ratio}")
            print(f"    Overall ratio: {overall_ratio_str}")
            print(f"    Prompt ({len(prompt)} chars):")
            print("    " + "\n    ".join(prompt.split("\n")))

            response = backend.images.generate(**kwargs_gen)

            # Decode image
            image_data = base64.b64decode(response.data[0].b64_json)

            # Prepare safe name for file operations
            safe_name = (
                character["name"]
                .replace(" ", "_")
                .replace("'", "")
                .replace("-", "_")
            )

            # Save composite if requested
            if args.save_composite:
                composite_path = output_dir / f"{safe_name}_composite.{output_ext}"
                with open(composite_path, "wb") as f:
                    f.write(image_data)
                print(f"  Saved composite to {composite_path}")

            # Detect and split subimages
            
            # Save composite temporarily for processing
            temp_composite = output_dir / f"temp_{safe_name}.png"
            with open(temp_composite, "wb") as f:
                f.write(image_data)

            try:
                subimages = detect_and_split_subimages(temp_composite, num_poses, layout)

                # Save individual images

                for idx, subimg in enumerate(subimages):
                    if idx < len(poses):
                        pose = poses[idx]
                        safe_pose = pose["name"].replace(" ", "_")
                        filename = f"{safe_name}_{safe_pose}.{output_ext}"
                        output_path = output_dir / filename

                        subimg.save(output_path, format=output_format.upper())
                        print(f"  Saved {filename}")
                        total += 1
            finally:
                # Clean up temp file
                if temp_composite.exists():
                    temp_composite.unlink()

        except Exception as e:
            print(f"  Error generating {character['name']}: {e}")
            import traceback

            traceback.print_exc()
            continue

    print(f"\nGenerated {total} image(s) successfully.")


if __name__ == "__main__":
    main()

