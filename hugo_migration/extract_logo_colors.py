# ============================================================================
# File: extract_logo_colors.py - Extract colors from logo
# ============================================================================

from PIL import Image
from collections import Counter
import colorsys
from pathlib import Path

def get_dominant_colors(image_path, num_colors=5):
    """Extract dominant colors from an image"""
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize((150, 150))  # Reduce size for faster processing
    
    pixels = list(img.getdata())
    
    # Get most common colors
    color_counter = Counter(pixels)
    dominant_colors = color_counter.most_common(num_colors)
    
    return [color for color, count in dominant_colors]

def rgb_to_hex(rgb):
    """Convert RGB to hex"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def get_color_brightness(rgb):
    """Calculate perceived brightness of a color"""
    return (rgb[0] * 299 + rgb[1] * 587 + rgb[2] * 114) / 1000

def main():
    print("=== Logo Color Extraction ===\n")
    
    
    logo_file = "/Users/almargolis/projects/tmih_hugo/static/images/TMIH_Logo_200x106.png"

    print(f"Found logo: {logo_file}")
    print("Extracting colors...\n")
    
    colors = get_dominant_colors(str(logo_file))
    
    print("Dominant colors from logo:")
    for i, color in enumerate(colors, 1):
        hex_color = rgb_to_hex(color)
        brightness = get_color_brightness(color)
        print(f"{i}. {hex_color} (RGB: {color}, Brightness: {brightness:.0f})")
    
    print("\nRecommended CSS variables:")
    print("Copy these to app/static/css/colors.css:\n")
    
    # Sort colors by brightness for better assignment
    sorted_colors = sorted(colors, key=get_color_brightness, reverse=True)
    
    print(":root {")
    print(f"    --primary-color: {rgb_to_hex(sorted_colors[1] if len(sorted_colors) > 1 else sorted_colors[0])};")
    print(f"    --secondary-color: {rgb_to_hex(sorted_colors[2] if len(sorted_colors) > 2 else sorted_colors[0])};")
    print(f"    --accent-color: {rgb_to_hex(sorted_colors[0])};")
    print("}")

if __name__ == '__main__':
    main()