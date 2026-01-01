# Werewolf Asset Generation

Multi-backend character image generation for the werewolf game. Supports OpenAI DALL-E and Google Gemini (Imagen) APIs to generate pixel art character images based on character configurations.

## Installation

This project uses `uv` for dependency management. Install dependencies with:

```bash
uv sync
```

## Setup

Set your API key as an environment variable based on which backend you want to use:

**For Gemini (default):**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**For OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Usage

Generate all characters with all poses (uses Gemini by default):

```bash
uv run python generate_characters.py
```

### Command-Line Options

- `--config`: Path to character configuration YAML file (default: `character_config.yaml`)
- `--name`: Character name to generate, or `all` for all characters (default: `all`)
- `--pose`: Pose name to generate, or `all` for all poses (default: `all`)
- `--size`: Image size in format WxH (default: `256x256`)
- `--reference-picture`: Optional reference image path (default: `None`)
- `--output-dir`: Output directory for generated images (default: `outputs`)
- `--jpeg`: Use JPEG format instead of PNG (default: PNG)
- `--backend`: Backend to use: `openai` or `gemini` (default: `gemini`)
- `--model`: Model to use (backend-specific):
  - OpenAI: `dall-e-2` or `dall-e-3` (default: `dall-e-2` when using OpenAI)
  - Gemini: `gemini-2.0-flash-exp` or other Imagen models (default: `gemini-2.0-flash-exp`)
- `--quality`: Image quality for DALL-E-3: `standard` or `hd` (default: `standard`)
- `--style`: Image style for DALL-E-3: `vivid` or `natural` (default: `vivid`)

### Examples

Generate a specific character and pose using Gemini (default):

```bash
uv run python generate_characters.py --name "Alice Adams" --pose smiling
```

Generate using OpenAI backend:

```bash
uv run python generate_characters.py --backend openai --name "Alice Adams" --pose smiling
```

Generate all poses for a specific character:

```bash
uv run python generate_characters.py --name "Baker Bob" --pose all
```

When generating all poses for a character (and no `--reference-picture` is provided), the script automatically uses the first generated pose as a reference for subsequent poses. This helps maintain consistency across poses of the same character. For example, when generating all poses for Alice:
1. First generates `Alice_Adams_smiling.png` (or the first pose in the config)
2. Uses that image as a reference when generating `Alice_Adams_angry.png`
3. Continues using the first image as reference for all remaining poses

This works with both OpenAI (DALL-E 2/3) and Gemini backends when reference images are supported.

Generate small images (256x256) with Gemini:

```bash
uv run python generate_characters.py --backend gemini --size 256x256
```

Generate with custom size and JPEG format:

```bash
uv run python generate_characters.py --size 512x512 --jpeg
```

Generate using OpenAI DALL-E 2 with a reference image:

```bash
uv run python generate_characters.py --backend openai --model dall-e-2 --reference-picture reference.png
```

Generate high-quality images with DALL-E 3:

```bash
uv run python generate_characters.py --backend openai --model dall-e-3 --quality hd --style vivid
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

## Backend Comparison

### Gemini (Imagen) - Default
- **Best for**: Small images (256x256, 512x512), modern models
- **Supported sizes**: 64x64 to 2048x2048 (flexible range)
- **Model**: `gemini-2.0-flash-exp` (default) or other Imagen models
- **Reference images**: Supported (may vary by model)
- **API Key**: `GOOGLE_API_KEY` environment variable
- **Advantages**: 
  - Supports smaller image sizes that DALL-E 3 doesn't
  - Modern Imagen models with high quality
  - Flexible size options

### OpenAI DALL-E 3
- **Best for**: Large, high-quality images
- **Supported sizes**: `1024x1024`, `1792x1024`, `1024x1792`
- **Model**: `dall-e-3`
- **Reference images**: Supported via image editing endpoint
- **Quality options**: `standard` or `hd`
- **Style options**: `vivid` or `natural`
- **API Key**: `OPENAI_API_KEY` environment variable
- **Advantages**: 
  - High-quality output
  - Advanced quality and style controls

### OpenAI GPT-Image-1
- **Best for**: Large, high-quality images with improved instruction following
- **Supported sizes**: `1024x1024`, `1792x1024`, `1024x1792`
- **Model**: `gpt-image-1`
- **Reference images**: Supported via image editing endpoint
- **Quality options**: `standard` or `hd`
- **Style options**: `vivid` or `natural`
- **API Key**: `OPENAI_API_KEY` environment variable
- **Advantages**: 
  - Native multimodal language model
  - Improved instruction following
  - More precise editing capabilities

### OpenAI DALL-E 2
- **Best for**: Medium-sized images, cost-effective
- **Supported sizes**: `256x256`, `512x512`, `1024x1024`
- **Model**: `dall-e-2`
- **Reference images**: Supported via image editing endpoint
- **API Key**: `OPENAI_API_KEY` environment variable
- **Advantages**: 
  - Lower cost than DALL-E 3
  - Supports medium sizes
  - Good reference image support

## When to Use Which Backend

- **Use Gemini** when:
  - You need small images (256x256, 512x512)
  - You want modern, high-quality models
  - You need flexible size options
  - You're generating pixel art or game assets

- **Use OpenAI DALL-E 3** when:
  - You need large, high-resolution images
  - You want maximum quality and style control
  - Size constraints allow 1024x1024 minimum

- **Use OpenAI DALL-E 2** when:
  - You need medium-sized images
  - Cost is a consideration
  - You need good reference image support

## Requirements

- Python >= 3.10
- API key for your chosen backend:
  - `GOOGLE_API_KEY` for Gemini backend
  - `OPENAI_API_KEY` for OpenAI backend
- Valid `character_config.yaml` file

## Dependencies

- `openai`: OpenAI Python SDK
- `google-genai`: Google Generative AI SDK (Gemini/Imagen)
- `pyyaml`: YAML file parsing
- `pillow`: Image processing
- `requests`: HTTP requests for image downloads
