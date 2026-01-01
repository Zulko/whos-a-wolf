# Werewolf Asset Generation

OpenAI-powered character image generation for the werewolf game. This module uses DALL-E to generate pixel art character images based on character configurations.

## Installation

This project uses `uv` for dependency management. Install dependencies with:

```bash
uv sync
```

## Setup

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

Generate all characters with all poses:

```bash
uv run python generate_characters.py
```

### Command-Line Options

- `--config`: Path to character configuration YAML file (default: `character_config.yaml`)
- `--name`: Character name to generate, or `all` for all characters (default: `all`)
- `--pose`: Pose name to generate, or `all` for all poses (default: `all`)
- `--size`: Image size in format WxH (default: `128x128`)
- `--reference-picture`: Optional reference image path (default: `None`)
- `--output-dir`: Output directory for generated images (default: `outputs`)
- `--jpeg`: Use JPEG format instead of PNG (default: PNG)
- `--model`: DALL-E model to use: `dall-e-2` or `dall-e-3` (default: `dall-e-3`)
- `--quality`: Image quality for DALL-E-3: `standard` or `hd` (default: `standard`)
- `--style`: Image style for DALL-E-3: `vivid` or `natural` (default: `vivid`)

### Examples

Generate a specific character and pose:

```bash
uv run python generate_characters.py --name "Alice Adams" --pose smiling
```

Generate all poses for a specific character:

```bash
uv run python generate_characters.py --name "Baker Bob" --pose all
```

When generating all poses for a character (and no `--reference-picture` is provided), the script automatically uses the first generated pose as a reference for subsequent poses. This helps maintain consistency across poses of the same character. For example, when generating all poses for Alice:
1. First generates `Alice_Adams_smiling.png` (or the first pose in the config)
2. Uses that image as a reference when generating `Alice_Adams_angry.png`
3. Continues using the first image as reference for all remaining poses

This works with both DALL-E 2 and DALL-E 3 using the image editing endpoint.

Generate with custom size and JPEG format:

```bash
uv run python generate_characters.py --size 512x512 --jpeg
```

Generate using DALL-E 2 with a reference image:

```bash
uv run python generate_characters.py --model dall-e-2 --reference-picture reference.png
```

Generate high-quality images:

```bash
uv run python generate_characters.py --model dall-e-3 --quality hd --style vivid
```

## Configuration File Format

The `character_config.yaml` file defines characters, their descriptions, backgrounds, and poses. The format is:

```yaml
context:
  - "Context description 1"
  - "Context description 2"

characters:
  - name: "Character Name"
    description: "Character appearance description"
    background: "Background description"
    dominant_color: "color"
    poses:
      - name: "pose_name"
        description: "Pose description"
```

### Example

```yaml
context:
  - All characters live in a 18th-century village.
  - This is for a kid-friendly werewolf game.
  - Use pixel art and cartoonish looks.

characters:
  - name: Alice Adams
    description: A young schoolgirl wearing black with black hair in ponytails.
    background: an old village street with limestone buildings
    dominant_color: limestone
    poses:
      - name: smiling
        description: smiling proudly, holding a small slate/primer book against her chest
```

## Output

Generated images are saved to the output directory (default: `outputs/`) with the naming format:

```
{output_dir}/{character_name}_{pose_name}.{extension}
```

Character names are normalized for filenames (spaces replaced with underscores, special characters removed).

## Model-Specific Notes

### DALL-E 3
- Supported sizes: `1024x1024`, `1792x1024`, `1024x1792`
- Supports `quality` (`standard` or `hd`) and `style` (`vivid` or `natural`) parameters
- Supports reference images via the image editing endpoint (`client.images.edit()`)

### DALL-E 2
- Supported sizes: `256x256`, `512x512`, `1024x1024`
- Supports reference images via the `--reference-picture` option (uses image editing endpoint)
- Automatically uses the first generated pose as reference when generating all poses for a character
- Does not support `quality` or `style` parameters (only available for DALL-E 3)

## Requirements

- Python >= 3.10
- OpenAI API key
- Valid `character_config.yaml` file

## Dependencies

- `openai`: OpenAI Python SDK
- `pyyaml`: YAML file parsing
- `pillow`: Image processing
- `requests`: HTTP requests for image downloads

