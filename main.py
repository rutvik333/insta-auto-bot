import os
import time
import requests
import feedparser
from PIL import Image
from duckduckgo_search import DDGS
from instagrapi import Client

def fetch_trending_news():
    print("Fetching trending entertainment news...")
    # Fetch top news from Google News RSS for movies/entertainment
    feed_url = "https://news.google.com/rss/search?q=Marvel+OR+Hollywood+OR+Movies+OR+Entertainment&hl=en-US&gl=US&ceid=US:en"
    feed = feedparser.parse(feed_url)
    
    if not feed.entries:
        raise Exception("No news found.")
        
    # Get the top entry
    top_entry = feed.entries[0]
    title = top_entry.title
    
    # Clean up the title (Google News appends " - Source Name")
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
        
    return title

def fetch_relevant_image(query):
    print(f"Searching for image relevant to: {query}")
    # Simplify query for better image results
    search_query = query.replace("'", "").replace('"', "")
    
    results = DDGS().images(search_query, max_results=5)
    
    for r in results:
        img_url = r.get('image')
        if not img_url: continue
        
        try:
            print(f"Downloading image: {img_url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(img_url, headers=headers, timeout=10)
            if response.status_code == 200:
                with open("raw_image.jpg", 'wb') as f:
                    f.write(response.content)
                return "raw_image.jpg"
        except Exception as e:
            print(f"Failed to download {img_url}: {e}")
            continue
            
    raise Exception("Could not download any relevant image.")

def format_image_for_instagram(image_path):
    print("Formatting image for Instagram (4:5 Portrait)...")
    width = 1080
    height = 1350
    
    img = Image.open(image_path).convert("RGB")
    
    # Resize and crop to fill 1080x1350
    img_ratio = img.width / img.height
    target_ratio = width / height
    
    if img_ratio > target_ratio:
        # Image is wider, crop sides
        new_width = int(target_ratio * img.height)
        offset = (img.width - new_width) // 2
        img = img.crop((offset, 0, offset + new_width, img.height))
    else:
        # Image is taller, crop top/bottom
        new_height = int(img.width / target_ratio)
        offset = (img.height - new_height) // 2
        img = img.crop((0, offset, img.width, offset + new_height))
        
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save("post.jpg", quality=95)
    return "post.jpg"

def post_to_instagram(image_path, headline):
    print("Logging into Instagram...")
    
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    
    if not username or not password:
        print("Missing IG_USERNAME or IG_PASSWORD environment variables. Skipping upload.")
        return
        
    cl = Client()
    try:
        # Delay to avoid aggressive blocking
        time.sleep(2)
        cl.login(username, password)
        
        caption = f"🚨 BREAKING NEWS 🚨\n\n{headline}\n\n#news #entertainment #marvel #hollywood #trending"
        print("Uploading photo...")
        cl.photo_upload(image_path, caption)
        print("Successfully posted to Instagram!")
    except Exception as e:
        print("Failed to post:", str(e))

if __name__ == "__main__":
    try:
        headline = fetch_trending_news()
        raw_img = fetch_relevant_image(headline)
        final_img = format_image_for_instagram(raw_img)
        post_to_instagram(final_img, headline)
    except Exception as e:
        print("Error:", str(e))
