import base64
from pathlib import Path
from typing import Union


def image_to_base64(
    image_path: Union[str, Path], include_mime_type: bool = True
) -> str:
    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Define supported image formats and their MIME types
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
    }

    file_extension = image_path.suffix.lower()

    if file_extension not in mime_types:
        raise ValueError(f"Unsupported image format: {file_extension}")

    # Read the image file in binary mode
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Encode to base64
    base64_encoded = base64.b64encode(image_data).decode("utf-8")

    if include_mime_type:
        mime_type = mime_types[file_extension]
        return f"{base64_encoded}"
    else:
        return base64_encoded


def base64_to_image(base64_string: str, output_path: Union[str, Path]) -> None:
    # Remove MIME type prefix if present
    if base64_string.startswith("data:"):
        # Format: data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEA...
        base64_string = base64_string.split(",", 1)[1]

    try:
        # Decode the base64 string
        image_data = base64.b64decode(base64_string)

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as image_file:
            image_file.write(image_data)

    except Exception as e:
        raise ValueError(f"Invalid base64 string or unable to save image: {e}")
