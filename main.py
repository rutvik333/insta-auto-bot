import os
import time
import requests
import feedparser
import urllib.parse
import textwrap
import re
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from instagrapi import Client

def download_font(url, filename):
    if not os.path.exists(filename):
        print(f"Downloading font {filename}...")
        r = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(r.content)

def fetch_trending_news():
    print("Fetching trending entertainment news...")
    feed_url = "https://news.google.com/rss/search?q=Marvel+OR+Hollywood+OR+Movies+OR+Entertainment&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        raise Exception("No news found.")
        
    top_entry = random.choice(feed.entries)
    title = top_entry.title
    
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
        
    # Clean HTML from summary for subhead
    summary = top_entry.get('summary', '')
    clean_sub = re.sub(r'<[^>]+>', '', summary)
    clean_sub = re.sub(r'&\w+;', ' ', clean_sub)
    clean_sub = " ".join(clean_sub.split())
    
    # If summary is too short or weird, use a generic one
    if len(clean_sub) < 20:
        clean_sub = "An unexpected reveal shakes up the entertainment industry in the latest trending news today."
        
    # Limit length
    if len(clean_sub) > 150:
        clean_sub = clean_sub[:147] + "..."
        
    return title, clean_sub

def fetch_relevant_image(query):
    print(f"Searching for image relevant to: {query}")
    img_url = None
    
    try:
        print("Scraping Bing Images...")
        search_query = query.replace("'", "").replace('"', "")
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(search_query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        html = requests.get(url, headers=headers, timeout=10).text
        m = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)
        if m:
            img_url = m[0]
    except Exception as e:
        print(f"Bing search failed: {e}")
            
    if not img_url:
        print("Using generic fallback.")
        img_url = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1080&auto=format&fit=crop"

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(img_url, headers=headers, timeout=10)
    if response.status_code == 200:
        with open("raw_image.jpg", 'wb') as f: f.write(response.content)
        return "raw_image.jpg"
    raise Exception("Could not download image.")

def format_image_for_instagram(image_path, headline, subhead):
    print("Applying text overlay and gradient...")
    width, height = 1080, 1350
    img = Image.open(image_path).convert("RGBA")
    
    # 1. Resize and crop
    img_ratio = img.width / img.height
    target_ratio = width / height
    if img_ratio > target_ratio:
        new_width = int(target_ratio * img.height)
        offset = (img.width - new_width) // 2
        img = img.crop((offset, 0, offset + new_width, img.height))
    else:
        new_height = int(img.width / target_ratio)
        offset = (img.height - new_height) // 2
        img = img.crop((0, offset, img.width, offset + new_height))
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # 2. Gradient Overlay (Darken bottom)
    gradient = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    for y in range(height):
        # Steeper gradient to leave top clear and bottom black
        alpha = int(255 * (y / height) ** 1.8)
        if alpha > 255: alpha = 255
        draw.line([(0, y), (width, y)], fill=(15, 20, 25, alpha))
    img = Image.alpha_composite(img, gradient)
    
    # 3. Fonts
    font_bold_url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Black.ttf"
    font_reg_url = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Medium.ttf"
    download_font(font_bold_url, "Montserrat-Black.ttf")
    download_font(font_reg_url, "Montserrat-Medium.ttf")
    
    font_large = ImageFont.truetype("Montserrat-Black.ttf", 85)
    font_small = ImageFont.truetype("Montserrat-Medium.ttf", 36)
    
    draw = ImageDraw.Draw(img)
    
    # 4. Text Formatting (Split headline)
    words = headline.split()
    mid = len(words) // 2
    part1 = " ".join(words[:mid]).upper()
    part2 = " ".join(words[mid:]).upper()
    
    part1_lines = textwrap.wrap(part1, width=18)
    part2_lines = textwrap.wrap(part2, width=18)
    
    # Calculate starting Y to keep it near bottom
    total_lines = len(part1_lines) + len(part2_lines)
    subhead_lines = textwrap.wrap(subhead, width=50)
    
    current_y = height - (len(subhead_lines) * 45) - (total_lines * 95) - 150
    
    # Draw White Part
    for line in part1_lines:
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_w = bbox[2] - bbox[0]
        draw.text(((width - text_w) / 2, current_y), line, font=font_large, fill=(255, 255, 255, 255))
        current_y += 95
        
    # Draw Blue Part
    for line in part2_lines:
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_w = bbox[2] - bbox[0]
        draw.text(((width - text_w) / 2, current_y), line, font=font_large, fill=(56, 189, 248, 255))
        current_y += 95
        
    current_y += 40
    
    # Sub-headline
    for line in subhead_lines:
        bbox = draw.textbbox((0, 0), line, font=font_small)
        text_w = bbox[2] - bbox[0]
        draw.text(((width - text_w) / 2, current_y), line, font=font_small, fill=(220, 220, 220, 255))
        current_y += 45
    
    # Logo Box at top right
    logo_txt = "VoxBulletin"
    bbox = draw.textbbox((0, 0), logo_txt, font=font_small)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    box_x = width - text_w - 70
    box_y = 50
    draw.rounded_rectangle([box_x - 30, box_y - 10, box_x + text_w + 20, box_y + text_h + 15], radius=25, fill=(0, 0, 0, 150), outline=(255, 255, 255, 40), width=2)
    draw.ellipse([box_x - 15, box_y + 12, box_x - 5, box_y + 22], fill=(56, 189, 248, 255))
    draw.text((box_x, box_y), logo_txt, font=font_small, fill=(255, 255, 255, 255))
    
    img = img.convert("RGB")
    img.save("post.jpg", quality=95)
    return "post.jpg"

def post_to_instagram(image_path, headline):
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    if not username or not password:
        raise Exception("Missing IG_USERNAME or IG_PASSWORD")
        
    cl = Client()
    time.sleep(2)
    cl.login(username, password)
    caption = f"🚨 BREAKING NEWS 🚨\n\n{headline}\n\n#news #entertainment #marvel #hollywood #trending"
    cl.photo_upload(image_path, caption)

if __name__ == "__main__":
    pass
