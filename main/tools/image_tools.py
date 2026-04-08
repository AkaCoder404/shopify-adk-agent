"""Image generation and manipulation tools for AI product photography."""

import base64
import os
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from main.tools.file_storage import get_generated_image_path, ensure_directories


def get_genai_client() -> genai.Client:
    """Get Google GenAI client with API key from environment."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    return genai.Client(api_key=api_key)


def generate_product_image(
    prompt: str,
    product_name: str,
    image_type: str = "hero",
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Generate a product image using Google Imagen API.
    
    Args:
        prompt: Detailed prompt describing the desired image
        product_name: Name of the product (for filename)
        image_type: Type of image - hero, detail, lifestyle, scale
        aspect_ratio: Aspect ratio - 1:1, 4:3, 16:9, etc.
        
    Returns:
        Dictionary with image path and metadata
    """
    client = get_genai_client()
    ensure_directories()
    
    # Enhance prompt for e-commerce quality
    enhanced_prompt = f"""
Professional e-commerce product photography: {prompt}

Requirements:
- Studio lighting, clean professional composition
- High-end retail catalog quality
- Sharp focus, commercial photography style
- Suitable for online store product listing
- No text, watermarks, or branding
""".strip()
    
    # Generate the image
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=enhanced_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["Text", "Image"],
        ),
    )
    
    # Extract image data
    image_data = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image_data = part.inline_data.data
            break
    
    if not image_data:
        raise RuntimeError("No image was generated")
    
    # Save the image
    safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_').lower()[:30]
    timestamp = os.urandom(4).hex()
    filename = f"{safe_name}_{image_type}_{timestamp}.png"
    
    image_path = get_generated_image_path(filename)
    
    with open(image_path, 'wb') as f:
        f.write(image_data)
    
    return {
        "image_path": str(image_path),
        "filename": filename,
        "image_type": image_type,
        "prompt_used": enhanced_prompt,
        "aspect_ratio": aspect_ratio,
    }


def edit_product_image(
    image_path: str,
    edit_prompt: str,
    product_name: str,
) -> dict:
    """
    Edit an existing product image using Google Imagen API.
    
    Args:
        image_path: Path to the source image
        edit_prompt: Instructions for editing the image
        product_name: Name of the product (for new filename)
        
    Returns:
        Dictionary with edited image path and metadata
    """
    client = get_genai_client()
    ensure_directories()
    
    # Read source image
    source_path = Path(image_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {image_path}")
    
    with open(source_path, 'rb') as f:
        image_data = f.read()
    
    # Create image content
    image_content = types.Content(
        parts=[
            types.Part(text=edit_prompt),
            types.Part(
                inline_data=types.Blob(
                    mime_type="image/png",
                    data=image_data,
                )
            ),
        ]
    )
    
    # Generate edited image
    response = client.models.generate_content(
        model="gemini-2.0-flash-preview-image-generation",
        contents=image_content,
        config=types.GenerateContentConfig(
            response_modalities=["Text", "Image"],
        ),
    )
    
    # Extract edited image data
    edited_image_data = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            edited_image_data = part.inline_data.data
            break
    
    if not edited_image_data:
        raise RuntimeError("No edited image was generated")
    
    # Save the edited image
    safe_name = "".join(c for c in product_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_').lower()[:30]
    timestamp = os.urandom(4).hex()
    filename = f"{safe_name}_edited_{timestamp}.png"
    
    edited_path = get_generated_image_path(filename)
    
    with open(edited_path, 'wb') as f:
        f.write(edited_image_data)
    
    return {
        "image_path": str(edited_path),
        "filename": filename,
        "original_image": image_path,
        "edit_prompt": edit_prompt,
    }


def generate_product_image_set(
    product_name: str,
    product_description: str,
    style: str = "studio",
) -> dict:
    """
    Generate a complete set of product images (hero, detail, lifestyle, scale).
    
    Args:
        product_name: Name of the product
        product_description: Product description for context
        style: Image style - studio, lifestyle, minimalist, luxury, etc.
        
    Returns:
        Dictionary with paths to all generated images
    """
    images = []
    
    # 1. Hero shot - clean background
    hero_prompt = f"""
{product_name} - Hero product shot on clean white background.
{product_description}
Style: {style}, professional studio photography, centered composition,
single product view, soft shadows, premium retail catalog quality.
"""
    hero_result = generate_product_image(
        prompt=hero_prompt,
        product_name=product_name,
        image_type="hero",
    )
    images.append(hero_result)
    
    # 2. Detail/texture shot
    detail_prompt = f"""
{product_name} - Close-up detail shot showing material texture and craftsmanship.
{product_description}
Style: {style}, macro photography style, sharp focus on details,
showing quality and texture, shallow depth of field.
"""
    detail_result = generate_product_image(
        prompt=detail_prompt,
        product_name=product_name,
        image_type="detail",
    )
    images.append(detail_result)
    
    # 3. Lifestyle/context shot
    lifestyle_prompt = f"""
{product_name} - Lifestyle context shot showing product in use or styled scene.
{product_description}
Style: {style}, aspirational lifestyle photography, natural setting,
beautiful composition, warm inviting atmosphere.
"""
    lifestyle_result = generate_product_image(
        prompt=lifestyle_prompt,
        product_name=product_name,
        image_type="lifestyle",
    )
    images.append(lifestyle_result)
    
    # 4. Scale/reference shot
    scale_prompt = f"""
{product_name} - Product shown with reference for scale and size.
{product_description}
Style: {style}, clean composition with scale reference, 
showing product dimensions clearly, professional catalog style.
"""
    scale_result = generate_product_image(
        prompt=scale_prompt,
        product_name=product_name,
        image_type="scale",
    )
    images.append(scale_result)
    
    return {
        "product_name": product_name,
        "style": style,
        "images": images,
        "image_paths": [img["image_path"] for img in images],
    }


def create_image_prompts(
    product_name: str,
    product_description: str,
    target_audience: Optional[str] = None,
    image_style: Optional[str] = None,
) -> dict:
    """
    Create professional image generation prompts for a product.
    
    Args:
        product_name: Name of the product
        product_description: Product description
        target_audience: Target customer demographic
        image_style: Desired visual style
        
    Returns:
        Dictionary with prompts for different image types
    """
    style = image_style or "studio"
    audience = target_audience or "general consumers"
    
    return {
        "hero": f"""
{product_name} - Professional e-commerce hero shot on pure white background.
{product_description}
Target audience: {audience}
Style: {style}, studio lighting, centered composition, commercial photography,
clean shadows, high-end retail catalog quality, 8k resolution.
""".strip(),
        "detail": f"""
{product_name} - Macro detail shot highlighting material quality and craftsmanship.
{product_description}
Target audience: {audience}
Style: {style}, extreme close-up, sharp focus on texture, shallow depth of field,
showing premium quality details, professional product photography.
""".strip(),
        "lifestyle": f"""
{product_name} - Lifestyle scene showing product in aspirational context.
{product_description}
Target audience: {audience}
Style: {style}, natural lighting, beautiful composition, aspirational setting,
warm inviting atmosphere, editorial quality photography.
""".strip(),
        "scale": f"""
{product_name} - Scale reference shot showing product size clearly.
{product_description}
Target audience: {audience}
Style: {style}, clean composition, product with scale reference object,
dimensional clarity, professional catalog photography.
""".strip(),
    }
