#!/usr/bin/env python3
"""
Simple script to generate an image from imgspec.md using GPT-5.
"""

import base64
import os
from pathlib import Path
from openai import OpenAI


def main():
    # Read the spec file
    spec_path = Path(__file__).parent / "imgspec.md"
    with open(spec_path, "r") as f:
        prompt = f.read()

    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    # Generate image using GPT-5 with image generation tool
    print("Generating image with GPT-5...")
    response = client.responses.create(
        model="gpt-5",
        input=prompt,
        tools=[
            {
                "type": "image_generation",
                "background": "transparent",
                "quality": "high",
            }
        ],
    )

    # Extract image data from response
    image_data = [
        output.result
        for output in response.output
        if output.type == "image_generation_call"
    ]

    if not image_data:
        raise ValueError("No image data found in GPT-5 response")

    image_base64 = image_data[0]

    # Decode and save the image
    output_path = Path(__file__).parent / "test.png"
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(image_base64))

    print(f"Image saved to {output_path}")


if __name__ == "__main__":
    main()
