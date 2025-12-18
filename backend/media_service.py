"""
Media Service - Multi-Source Image Integration
Handles image search and processing from DuckDuckGo, Wikipedia, and external APIs
Processes image tags in AI responses for both text and voice modes
"""
import os
import re
import requests
from typing import Optional, List, Dict
from duckduckgo_search import DDGS

def search_duckduckgo_images(query: str, max_results: int = 1) -> Optional[str]:
    """
    Search for images using DuckDuckGo
    Returns the first image URL or None
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(
                keywords=query,
                max_results=max_results,
                safesearch='on'  # Always use safe search for students
            ))
            
            if results and len(results) > 0:
                return results[0].get('image')
    except Exception as e:
        print(f"DuckDuckGo image search error: {e}")
    
    return None


def search_wikipedia_images(query: str) -> Optional[str]:
    """
    Search for images using Wikipedia API
    Returns the first image URL or None
    """
    try:
        import wikipedia
        
        # Search for the page
        search_results = wikipedia.search(query, results=1)
        if not search_results:
            return None
        
        # Get the page
        page = wikipedia.page(search_results[0], auto_suggest=False)
        
        # Get images from the page
        if page.images and len(page.images) > 0:
            # Filter for common image formats
            for img_url in page.images:
                if any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    return img_url
    except Exception as e:
        print(f"Wikipedia image search error: {e}")
    
    return None


def search_image_multi_source(query: str) -> Optional[str]:
    """
    Search for images using multiple sources with fallback chain
    Priority: DuckDuckGo → Wikipedia
    Returns the first successful image URL or None
    """
    # Try DuckDuckGo first (fastest and most reliable)
    image_url = search_duckduckgo_images(query)
    if image_url:
        print(f"✅ Found image via DuckDuckGo: {query}")
        return image_url
    
    # Fallback to Wikipedia
    image_url = search_wikipedia_images(query)
    if image_url:
        print(f"✅ Found image via Wikipedia: {query}")
        return image_url
    
    print(f"⚠️ No image found for: {query}")
    return None


def process_image_tags(text: str) -> str:
    """
    Process [SHOW_IMAGE: query] tags in AI responses
    Replaces tags with actual image HTML for text mode
    """
    if not text:
        return text
    
    # Find all image tags
    pattern = r'\[SHOW_IMAGE:\s*([^\]]+)\]'
    matches = re.findall(pattern, text)
    
    if not matches:
        return text
    
    # Process each tag
    for query in matches:
        query = query.strip()
        
        # Search for image
        image_url = search_image_multi_source(query)
        
        if image_url:
            # Replace tag with HTML image
            img_html = f'<img src="{image_url}" alt="{query}" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0;" />'
            text = text.replace(f'[SHOW_IMAGE: {query}]', img_html)
        else:
            # Remove tag if no image found
            text = text.replace(f'[SHOW_IMAGE: {query}]', f'[Image: {query} - not available]')
    
    return text


def strip_markdown_for_voice(text: str) -> str:
    """
    Strip markdown formatting and convert to plain text for voice output
    Removes: **, *, ##, HTTP links, image tags
    Converts image tags to descriptive text
    """
    if not text:
        return text
    
    # Convert image tags to descriptive text
    pattern = r'\[SHOW_IMAGE:\s*([^\]]+)\]'
    text = re.sub(pattern, r'Here is an image of \1.', text)
    
    # Remove HTML image tags (in case they were already processed)
    text = re.sub(r'<img[^>]*>', '', text)
    
    # Remove markdown bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    
    # Remove markdown italic
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove HTTP/HTTPS links but keep the text
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # Remove markdown code blocks
    text = re.sub(r'`([^`]+)`', r'\1', text)
    
    # Remove bullet points
    text = re.sub(r'^[-*•]\s+', '', text, flags=re.MULTILINE)
    
    # Remove numbered lists
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def prepare_voice_response(ai_response: str) -> str:
    """
    Prepare AI response for voice output
    Strips markdown and converts to natural speech text
    """
    return strip_markdown_for_voice(ai_response)


def prepare_text_response(ai_response: str) -> str:
    """
    Prepare AI response for text output
    Processes image tags and keeps markdown formatting
    """
    return process_image_tags(ai_response)
