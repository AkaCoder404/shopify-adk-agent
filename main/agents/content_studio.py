"""Content Studio Agent - AI content generation pipeline."""

from google.adk.agents import Agent, SequentialAgent

from main.tools.image_tools import (
    generate_product_image,
    edit_product_image,
    generate_product_image_set,
    create_image_prompts,
)


# Text Generator Agent - Creates titles and descriptions
text_generator = Agent(
    name="text_generator",
    model="gemini-2.5-pro",
    description="Generates store-ready product titles and descriptions from supplier text.",
    instruction="""
You are a creative copywriter specializing in e-commerce product content.

Your task: Transform supplier product information into compelling, store-ready content.

Input (from session state):
- original_title: Supplier's product title
- original_description: Supplier's description
- target_audience: (optional) Who this product is for
- tone: (optional) Style - professional, casual, luxury, playful, etc.

Output (set in session state):
- generated_title: Optimized product title (50-70 chars ideal)
- generated_description: Marketing-ready HTML description
- key_features: List of key selling points
- target_keywords: SEO keywords for the product

Guidelines:
- Title should be concise, include key product type and differentiator
- Description should be engaging, benefit-focused, and SEO-friendly
- Use HTML formatting for description (<p>, <ul>, <li>, <strong>)
- Match the requested tone or default to professional
- Highlight unique selling points
- Include relevant keywords naturally
""",
    output_key="generated_text_content",
)


# Image Generator Agent - Creates product images
image_generator = Agent(
    name="image_generator",
    model="gemini-2.5-flash",
    description="Generates and edits product images using AI.",
    instruction="""
You are a product photography specialist using AI image generation.

Your task: Generate studio-quality product images from text descriptions or edit existing images.

Input (from session state):
- product_name: Name of the product
- generated_title: Optimized title (for context)
- generated_description: Description (for context)
- original_image_url: (optional) Source image to edit/improve
- image_style: (optional) Desired style - studio, lifestyle, minimalist, luxury, etc.

Output (set in session state):
- generated_image_paths: List of paths to generated images
- image_prompts_used: List of prompts used for generation

Guidelines:
- Generate multiple angles when possible:
  1. Hero shot on clean background
  2. Detail/texture close-up
  3. Lifestyle/context shot (if applicable)
  4. Scale/reference shot
- Use descriptive prompts mentioning lighting, background, angle
- Save images to workspace/images/generated/
- Return full paths to generated files

Available Tools:
- generate_product_image: Generate a single image from text prompt
- generate_product_image_set: Generate complete set (hero, detail, lifestyle, scale)
- edit_product_image: Edit an existing image
- create_image_prompts: Create professional prompts for image generation

Workflow:
1. First use create_image_prompts to generate professional prompts
2. Then use generate_product_image_set to create all 4 images
3. Save results to session state
""",
    tools=[
        generate_product_image,
        generate_product_image_set,
        edit_product_image,
        create_image_prompts,
    ],
    output_key="generated_image_content",
)


# SEO Optimizer Agent - Enhances content for search
seo_optimizer = Agent(
    name="seo_optimizer",
    model="gemini-2.5-flash",
    description="Optimizes product content for search engines.",
    instruction="""
You are an SEO specialist for e-commerce.

Your task: Optimize product content for maximum search visibility.

Input (from session state):
- generated_title: AI-generated title
- generated_description: AI-generated description
- key_features: Extracted features
- target_keywords: Suggested keywords

Output (set in session state):
- seo_title: Final SEO-optimized title (< 60 chars)
- seo_description: Meta description (< 160 chars)
- optimized_description: Enhanced product description with SEO
- seo_tags: List of tags for Shopify
- search_keywords: Primary and secondary keywords

SEO Guidelines:
- Title: Include primary keyword near beginning, keep under 60 chars
- Meta Description: Compelling, include keywords, under 160 chars
- Description: Use H2/H3 headers, bullet points, keyword-rich but natural
- Tags: Mix of broad and specific terms customers might search
- URL Handle: Suggest SEO-friendly handle

Output should be ready for direct use in Shopify product creation.
""",
    output_key="seo_optimized_content",
)


# Content Studio - Sequential pipeline combining all content agents
content_studio_agent = SequentialAgent(
    name="content_studio",
    sub_agents=[text_generator, image_generator, seo_optimizer],
    description="End-to-end content generation pipeline: text → images → SEO optimization.",
)
