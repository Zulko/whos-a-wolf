#!/usr/bin/env python3
"""
Generate character images using OpenAI DALL-E or Google Gemini Imagen API.
"""

import argparse
import os
import base64
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict, Any
from io import BytesIO

import yaml
from openai import OpenAI
from google import genai


def parse_size(size_str: str) -> tuple[int, int]:
    """Parse size string like '128x128' into (width, height) tuple."""
    try:
        width, height = map(int, size_str.lower().split("x"))
        return width, height
    except ValueError:
        raise ValueError(
            f"Invalid size format: {size_str}. Expected format: WxH (e.g., 128x128)"
        )


def build_prompt(
    character: Dict[str, Any], pose: Dict[str, Any], context: List[str]
) -> str:
    """Build a prompt for image generation from character and pose data."""
    context_str = " ".join(context)
    prompt_parts = [
        context_str,
        character["description"],
        f"Background: {character['background']}",
        f"Pose: {pose['description']}",
        "Pixel art style, cartoonish, kid-friendly",
    ]
    return ". ".join(prompt_parts) + "."


class ImageBackend(ABC):
    """Abstract base class for image generation backends."""

    @abstractmethod
    def generate_image(
        self,
        prompt: str,
        size: tuple[int, int],
        reference_image: Optional[Path] = None,
        **kwargs,
    ) -> bytes:
        """Generate an image and return as bytes."""
        pass

    @abstractmethod
    def supports_size(self, size: tuple[int, int]) -> bool:
        """Check if the backend supports the given size."""
        pass

    @abstractmethod
    def supports_reference_images(self) -> bool:
        """Check if the backend supports reference images."""
        pass


class OpenAIBackend(ImageBackend):
    """OpenAI DALL-E backend implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "dall-e-2",
        quality: Optional[str] = None,
        style: Optional[str] = None,
    ):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.quality = quality
        self.style = style

    def supports_size(self, size: tuple[int, int]) -> bool:
        """Check if OpenAI model supports the given size."""
        size_str = f"{size[0]}x{size[1]}"
        valid_sizes = self._get_valid_sizes()
        return size_str in valid_sizes if valid_sizes else True

    def _get_valid_sizes(self) -> List[str]:
        """Get valid size options for the current model."""
        if self.model.startswith("dall-e-3"):
            return ["1024x1024", "1792x1024", "1024x1792"]
        elif self.model.startswith("gpt-image-1"):
            return ["1024x1024", "1024x1536", "1536x1024", "auto"]
        elif self.model.startswith("dall-e-2"):
            return ["256x256", "512x512", "1024x1024"]
        return []

    def supports_reference_images(self) -> bool:
        """OpenAI supports reference images via image editing endpoint."""
        return True

    def generate_image(
        self,
        prompt: str,
        size: tuple[int, int],
        reference_image: Optional[Path] = None,
        **kwargs,
    ) -> bytes:
        """Generate an image using OpenAI API."""
        size_str = f"{size[0]}x{size[1]}"
        output_format = kwargs.get("output_format", "b64_json")

        # Validate size for model
        valid_sizes = self._get_valid_sizes()
        if valid_sizes and size_str not in valid_sizes:
            raise ValueError(
                f"Size {size_str} not valid for {self.model}. Valid sizes: {', '.join(valid_sizes)}"
            )

        # Handle reference image - use image editing endpoint
        if reference_image:
            with open(reference_image, "rb") as img_file:
                edit_kwargs = {
                    "model": self.model,
                    "image": img_file,
                    "prompt": prompt,
                    "size": size_str,
                    "n": 1,
                }
                # Only DALL-E models support response_format
                if not self.model.startswith("gpt-image-1"):
                    edit_kwargs["response_format"] = output_format
                # DALL-E 3 supports quality and style in edit endpoint
                if self.model.startswith("dall-e-3"):
                    if self.quality:
                        edit_kwargs["quality"] = self.quality
                    if self.style:
                        edit_kwargs["style"] = self.style
                # GPT-Image-1 supports quality but not style
                elif self.model.startswith("gpt-image-1"):
                    if self.quality:
                        edit_kwargs["quality"] = self.quality
                response = self.client.images.edit(**edit_kwargs)

                # Handle edit response - GPT-Image-1 returns URLs by default
                if self.model.startswith("gpt-image-1"):
                    import requests

                    img_response = requests.get(response.data[0].url)
                    return img_response.content
                elif output_format == "b64_json":
                    return base64.b64decode(response.data[0].b64_json)
                else:
                    import requests

                    img_response = requests.get(response.data[0].url)
                    return img_response.content
        else:
            # Standard text-to-image generation
            kwargs_gen = {
                "model": self.model,
                "prompt": prompt,
                "size": size_str,
                "n": 1,
            }
            # Only DALL-E models support response_format
            if not self.model.startswith("gpt-image-1"):
                kwargs_gen["response_format"] = output_format
            # DALL-E 3 supports quality and style
            if self.model.startswith("dall-e-3"):
                if self.quality:
                    kwargs_gen["quality"] = self.quality
                if self.style:
                    kwargs_gen["style"] = self.style
            # GPT-Image-1 supports quality but not style
            elif self.model.startswith("gpt-image-1"):
                if self.quality:
                    kwargs_gen["quality"] = self.quality

            response = self.client.images.generate(**kwargs_gen)

        # Handle response based on format
        # GPT-Image-1 returns URLs by default (no response_format support)
        # DALL-E models can return b64_json if requested
        if self.model.startswith("gpt-image-1"):
            # GPT-Image-1 always returns URLs
            import requests

            img_response = requests.get(response.data[0].url)
            return img_response.content
        elif output_format == "b64_json":
            return base64.b64decode(response.data[0].b64_json)
        else:
            # URL format - download the image
            import requests

            img_response = requests.get(response.data[0].url)
            return img_response.content


def size_to_aspect_ratio(size: tuple[int, int]) -> str:
    """Convert a size tuple to a valid Gemini aspect ratio string."""
    width, height = size
    aspect = width / height

    # Valid aspect ratios for Gemini Imagen API
    valid_ratios = {
        "1:1": 1.0,
        "4:5": 0.8,
        "5:4": 1.25,
        "3:4": 0.75,
        "4:3": 1.333,
        "2:3": 0.667,
        "3:2": 1.5,
        "9:16": 0.5625,
        "16:9": 1.778,
        "21:9": 2.333,
    }

    # Find the closest valid aspect ratio
    closest_ratio = "1:1"
    min_diff = float("inf")

    for ratio_str, ratio_value in valid_ratios.items():
        diff = abs(aspect - ratio_value)
        if diff < min_diff:
            min_diff = diff
            closest_ratio = ratio_str

    return closest_ratio


class GeminiBackend(ImageBackend):
    """Google Gemini Imagen backend implementation."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def supports_size(self, size: tuple[int, int]) -> bool:
        """Gemini/Imagen supports various sizes including small ones."""
        # Gemini supports a wide range of sizes, including small ones like 256x256
        # We'll allow most reasonable sizes
        width, height = size
        return width >= 64 and height >= 64 and width <= 2048 and height <= 2048

    def supports_reference_images(self) -> bool:
        """Gemini may support reference images, but implementation may differ."""
        # For now, we'll implement basic support
        return True

    def generate_image(
        self,
        prompt: str,
        size: tuple[int, int],
        reference_image: Optional[Path] = None,
        **kwargs,
    ) -> bytes:
        """Generate an image using Gemini Imagen API."""
        width, height = size

        # Build the prompt with size specification
        size_prompt = f"{width}x{height} pixel image"
        full_prompt = f"{prompt} {size_prompt}."

        # Convert size to valid aspect ratio
        aspect_ratio = size_to_aspect_ratio(size)

        # Prepare generation config
        generation_config = {
            "image_config": {
                "aspect_ratio": aspect_ratio,
            }
        }

        # Handle reference image if provided
        if reference_image:
            # Read reference image
            with open(reference_image, "rb") as f:
                reference_data = f.read()

            # Gemini can use reference images in the prompt
            # We'll include it as part of the content
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "inline_data": {
                                        "mime_type": "image/png",
                                        "data": reference_data,
                                    }
                                },
                                {"text": full_prompt},
                            ],
                        }
                    ],
                    config=generation_config,
                )
            except Exception as e:
                # If reference image doesn't work, fall back to text-only
                print(
                    f"  Warning: Reference image not supported, using text prompt only: {e}"
                )
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config=generation_config,
                )
        else:
            # Standard text-to-image generation
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=generation_config,
            )

        # Extract image from response
        for part in response.parts:
            # Try as_image() method first (most reliable)
            if hasattr(part, "as_image"):
                try:
                    img = part.as_image()
                    if img is not None:
                        buf = BytesIO()
                        img.save(buf, format="PNG")
                        return buf.getvalue()
                except Exception:
                    # Continue to try other methods
                    pass

            # Check for inline_data attribute
            try:
                inline_data = part.inline_data
                if inline_data is not None:
                    # Try accessing data attribute
                    if hasattr(inline_data, "data"):
                        data = inline_data.data
                        if data:
                            # If data is bytes, return it directly
                            if isinstance(data, bytes):
                                return data
                            # If data is base64 encoded string, decode it
                            elif isinstance(data, str):
                                return base64.b64decode(data)

                    # Try accessing mime_type and data as dict-like
                    if hasattr(inline_data, "get"):
                        data = inline_data.get("data")
                        if data:
                            if isinstance(data, bytes):
                                return data
                            elif isinstance(data, str):
                                return base64.b64decode(data)
            except (AttributeError, TypeError):
                pass

            # Try accessing part.data directly
            if hasattr(part, "data"):
                try:
                    data = part.data
                    if data is not None:
                        if isinstance(data, bytes):
                            return data
                        elif isinstance(data, str):
                            return base64.b64decode(data)
                except (AttributeError, TypeError):
                    pass

        # If we get here, we couldn't extract the image
        # Print debug info to help diagnose
        debug_info = []
        for i, p in enumerate(response.parts):
            debug_info.append(f"Part {i}:")
            debug_info.append(f"  Type: {type(p).__name__}")
            debug_info.append(f"  Has inline_data: {hasattr(p, 'inline_data')}")
            if hasattr(p, "inline_data"):
                try:
                    debug_info.append(f"  inline_data value: {p.inline_data}")
                    debug_info.append(f"  inline_data type: {type(p.inline_data)}")
                except:
                    debug_info.append(f"  inline_data access failed")
            debug_info.append(f"  Has as_image: {hasattr(p, 'as_image')}")
            if hasattr(p, "as_image"):
                try:
                    img = p.as_image()
                    debug_info.append(f"  as_image() result: {img}")
                    debug_info.append(
                        f"  as_image() type: {type(img) if img else None}"
                    )
                except Exception as e:
                    debug_info.append(f"  as_image() error: {e}")
            debug_info.append(f"  Has text: {hasattr(p, 'text')}")
            if hasattr(p, "text"):
                try:
                    text = p.text
                    debug_info.append(f"  text: {text[:100] if text else None}")
                except:
                    pass

        raise ValueError(
            f"No image data found in Gemini response.\n" + "\n".join(debug_info)
        )


def create_backend(backend_name: str, **kwargs) -> ImageBackend:
    """Factory function to create the appropriate backend."""
    if backend_name == "openai":
        api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return OpenAIBackend(
            api_key=api_key,
            model=kwargs.get("model", "dall-e-2"),
            quality=kwargs.get("quality"),
            style=kwargs.get("style"),
        )
    elif backend_name == "gemini":
        api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        return GeminiBackend(
            api_key=api_key,
            model=kwargs.get("model", "gemini-2.0-flash-exp"),
        )
    else:
        raise ValueError(f"Unknown backend: {backend_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate character images using OpenAI DALL-E or Google Gemini Imagen API"
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
        "--backend",
        type=str,
        choices=["openai", "gemini"],
        default="openai",
        help="Image generation backend to use: openai or gemini (default: openai)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (backend-specific): dall-e-2/dall-e-3/gpt-image-1 for OpenAI, gemini-2.0-flash-exp for Gemini",
    )
    parser.add_argument(
        "--quality",
        type=str,
        default=None,
        help="Image quality: 'standard' or 'hd' for DALL-E-3, 'low', 'medium', 'high', or 'auto' for GPT-Image-1 (default: 'standard' for DALL-E-3, 'high' for GPT-Image-1)",
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=["vivid", "natural"],
        default="vivid",
        help="Image style for DALL-E-3: vivid or natural (default: vivid)",
    )

    args = parser.parse_args()

    # Set default model based on backend
    if args.model is None:
        if args.backend == "openai":
            args.model = "dall-e-3"
        elif args.backend == "gemini":
            args.model = "gemini-2.0-flash-exp"

    # Set default size based on model if using default size
    # GPT-Image-1 and DALL-E 3 don't support small sizes, so use 1024x1024
    if args.size == "256x256" and (
        args.model.startswith("gpt-image-1") or args.model.startswith("dall-e-3")
    ):
        print(
            f"Warning: {args.model} doesn't support 256x256. Using 1024x1024 instead."
        )
        args.size = "1024x1024"

    # Set default quality based on model if not specified
    if args.quality is None:
        if args.model.startswith("gpt-image-1"):
            args.quality = "high"
        elif args.model.startswith("dall-e-3"):
            args.quality = "standard"
        else:
            args.quality = None  # DALL-E 2 doesn't support quality

    # Create backend
    backend_kwargs = {
        "model": args.model,
    }
    if args.backend == "openai":
        backend_kwargs["quality"] = args.quality
        backend_kwargs["style"] = args.style

    try:
        backend = create_backend(args.backend, **backend_kwargs)
    except ValueError as e:
        parser.error(str(e))

    # Parse size
    try:
        size = parse_size(args.size)
    except ValueError as e:
        parser.error(str(e))

    # Validate size for backend
    if not backend.supports_size(size):
        parser.error(f"Size {args.size} is not supported by {args.backend} backend")

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

    # Prepare reference image path
    reference_image = Path(args.reference_picture) if args.reference_picture else None
    if reference_image and not reference_image.exists():
        raise FileNotFoundError(f"Reference image not found: {reference_image}")

    # Check if backend supports reference images
    if reference_image and not backend.supports_reference_images():
        print(
            f"Warning: {args.backend} backend does not support reference images. Ignoring --reference-picture."
        )
        reference_image = None

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine output format
    output_format = "jpeg" if args.jpeg else "png"

    # Generate images
    total = 0
    generating_all_poses = args.pose.lower() == "all"
    use_auto_reference = (
        generating_all_poses
        and reference_image is None
        and backend.supports_reference_images()
    )

    for character in characters:
        poses = character.get("poses", [])

        # Filter poses
        if args.pose.lower() != "all":
            poses = [p for p in poses if p["name"].lower() == args.pose.lower()]
            if not poses:
                print(
                    f"Warning: Pose '{args.pose}' not found for character '{character['name']}'"
                )
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
                image_data = backend.generate_image(
                    prompt=prompt,
                    size=size,
                    reference_image=current_reference,
                    output_format="b64_json" if args.backend == "openai" else None,
                )

                # Save image
                # Normalize character name for filename (remove spaces, special chars)
                safe_name = (
                    character["name"]
                    .replace(" ", "_")
                    .replace("'", "")
                    .replace("-", "_")
                )
                safe_pose = pose["name"].replace(" ", "_")
                filename = f"{safe_name}_{safe_pose}.{output_format}"
                output_path = output_dir / filename

                with open(output_path, "wb") as f:
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
