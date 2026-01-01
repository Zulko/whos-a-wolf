Let's start a new module for asset generation. The module will use the OpenAI API to generate pictures of characters, from an input like character_config.json in this folder.

I want to be able to generate a picture as follows:

generate_characters.py --config character_config.yaml --name Alice --pose smiling --size 128x128 --reference-picture some_picture.png --output_dir outputs/ --jpeg

defaults:
size 128x128
name: all
pose: all
reference_picture: None
output_dir: outputs
jpeg: false: # PNG by default.

The resulting pictures will be stored in {outputs*dir}/{name}*{pose}.{extension}

Make this folder a proper python project with a pyproject.toml on the model of the one in puzzle_generation (but different dependencies).

Use the OpenAI sdk, assume the user has a openai key in their environment. Add any options related to that api you see fit.

Add a readme.
