#!/usr/bin/env python3
"""
Generate character images using OpenAI's DALL-E API.
"""

import argparse
import os
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml
from openai import OpenAI


def parse_size(size_str: str) -> tuple[int, int]:
    """Parse size string like '128x128' into (width, height) tuple."""
    try:
        width, height = map(int, size_str.lower().split('x'))
        return width, height
    except ValueError:
        raise ValueError(f"Invalid size format: {size_str}. Expected format: WxH (e.g., 128x128)")


def build_prompt(character: Dict[str, Any], pose: Dict[str, Any], context: List[str]) -> str:
    """Build a prompt for image generation from character and pose data."""
    context_str = " ".join(context)
    prompt_parts = [
        context_str,
        character['description'],
        f"Background: {character['background']}",
        f"Pose: {pose['description']}",
        "Pixel art style, cartoonish, kid-friendly",
    ]
    return ". ".join(prompt_parts) + "."


def get_valid_sizes(model: str) -> List[str]:
    """Get valid size options for a given model."""
    if model.startswith("dall-e-3"):
        return ["1024x1024", "1792x1024", "1024x1792"]
    elif model.startswith("dall-e-2"):
        return ["256x256", "512x512", "1024x1024"]
    return []


def generate_image(
    client: OpenAI,
    prompt: str,
    model: str,
    size: tuple[int, int],
    quality: Optional[str],
    style: Optional[str],
    reference_image: Optional[Path],
    output_format: str,
) -> bytes:
    """Generate an image using OpenAI API."""
    size_str = f"{size[0]}x{size[1]}"
    
    # Validate size for model
    valid_sizes = get_valid_sizes(model)
    if valid_sizes and size_str not in valid_sizes:
        raise ValueError(
            f"Size {size_str} not valid for {model}. Valid sizes: {', '.join(valid_sizes)}"
        )
    
    # Handle reference image - use image editing endpoint
    if reference_image:
        # Use image editing endpoint - pass file path directly
        with open(reference_image, "rb") as img_file:
            edit_kwargs = {
                "model": model,
                "image": img_file,
                "prompt": prompt,
                "size": size_str,
                "n": 1,
                "response_format": output_format,
            }
            # DALL-E 3 supports quality and style in edit endpoint
            if model.startswith("dall-e-3"):
                if quality:
                    edit_kwargs["quality"] = quality
                if style:
                    edit_kwargs["style"] = style
            response = client.images.edit(**edit_kwargs)
    else:
        # Standard text-to-image generation
        kwargs = {
            "model": model,
            "prompt": prompt,
            "size": size_str,
            "n": 1,
            "response_format": output_format,
        }
        if model.startswith("dall-e-3"):
            if quality:
                kwargs["quality"] = quality
            if style:
                kwargs["style"] = style
        
        response = client.images.generate(**kwargs)
    
    if output_format == "b64_json":
        return base64.b64decode(response.data[0].b64_json)
    else:
        # URL format - download the image
        import requests
        img_response = requests.get(response.data[0].url)
        return img_response.content


def main():
    parser = argparse.ArgumentParser(
        description="Generate character images using OpenAI's DALL-E API"
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
        "--pose",
        type=str,
        default="all",
        help="Pose name to generate, or 'all' for all poses (default: all)",
    )
    parser.add_argument(
        "--size",
        type=str,
        default="256x256",
        help="Image size in format WxH (default: 256x256)",
    )
    parser.add_argument(
        "--reference-picture",
        type=str,
        default=None,
        help="Optional reference image path (default: None)",
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
        "--model",
        type=str,
        default="dall-e-2",
        help="DALL-E model to use: dall-e-2 or dall-e-3 (default: dall-e-2)",
    )
    parser.add_argument(
        "--quality",
        type=str,
        choices=["standard", "hd"],
        default="standard",
        help="Image quality for DALL-E-3: standard or hd (default: standard)",
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=["vivid", "natural"],
        default="vivid",
        help="Image style for DALL-E-3: vivid or natural (default: vivid)",
    )
    
    args = parser.parse_args()
    
    # Validate OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = OpenAI(api_key=api_key)
    
    # Parse size
    try:
        size = parse_size(args.size)
    except ValueError as e:
        parser.error(str(e))
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    context = config.get('context', [])
    characters = config.get('characters', [])
    
    # Filter characters
    if args.name.lower() != "all":
        characters = [c for c in characters if c['name'].lower() == args.name.lower()]
        if not characters:
            raise ValueError(f"Character '{args.name}' not found in config")
    
    # Prepare reference image path
    reference_image = Path(args.reference_picture) if args.reference_picture else None
    if reference_image and not reference_image.exists():
        raise FileNotFoundError(f"Reference image not found: {reference_image}")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine output format
    output_format = "jpeg" if args.jpeg else "png"
    api_response_format = "b64_json"  # Always use base64 for easier handling
    
    # Generate images
    total = 0
    generating_all_poses = args.pose.lower() == "all"
    use_auto_reference = generating_all_poses and reference_image is None
    
    for character in characters:
        poses = character.get('poses', [])
        
        # Filter poses
        if args.pose.lower() != "all":
            poses = [p for p in poses if p['name'].lower() == args.pose.lower()]
            if not poses:
                print(f"Warning: Pose '{args.pose}' not found for character '{character['name']}'")
                continue
        
        # Track first generated image for this character (for auto-reference)
        first_pose_image = None
        
        for idx, pose in enumerate(poses):
            prompt = build_prompt(character, pose, context)
            
            # Determine reference image to use
            current_reference = reference_image
            if use_auto_reference and idx > 0 and first_pose_image:
                # Use the first generated pose as reference for subsequent poses
                current_reference = first_pose_image
            
            print(f"Generating {character['name']} - {pose['name']}...")
            if current_reference and idx > 0:
                print(f"  Using {first_pose_image.name} as reference")
            
            try:
                # Generate image
                image_data = generate_image(
                    client=client,
                    prompt=prompt,
                    model=args.model,
                    size=size,
                    quality=args.quality if args.model.startswith("dall-e-3") else None,
                    style=args.style if args.model.startswith("dall-e-3") else None,
                    reference_image=current_reference,
                    output_format=api_response_format,
                )
                
                # Save image
                # Normalize character name for filename (remove spaces, special chars)
                safe_name = character['name'].replace(' ', '_').replace("'", "").replace("-", "_")
                safe_pose = pose['name'].replace(' ', '_')
                filename = f"{safe_name}_{safe_pose}.{output_format}"
                output_path = output_dir / filename
                
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                
                print(f"  Saved to {output_path}")
                total += 1
                
                # Store first pose image path for use as reference
                if use_auto_reference and idx == 0:
                    first_pose_image = output_path
                
            except Exception as e:
                print(f"  Error generating {character['name']} - {pose['name']}: {e}")
                continue
    
    print(f"\nGenerated {total} image(s) successfully.")


if __name__ == "__main__":
    main()

