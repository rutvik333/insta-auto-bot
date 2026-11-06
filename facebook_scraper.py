import json
import re
import sys
import os
import webbrowser
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from curl_cffi import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SCRIPT_DIR, "last_seen_post.json")

def format_time_ago(ts):
    if not ts:
        return "Unknown"
    now_ts = datetime.now(timezone.utc).timestamp()
    diff = int(now_ts - ts)
    if diff < 0:
        return "Just now"
    if diff < 60:
        return f"{diff}s ago"
    elif diff < 3600:
        return f"{diff // 60}m ago"
    elif diff < 86400:
        return f"{diff // 3600}h ago"
    else:
        return f"{diff // 86400}d ago"

def fetch_facebook_html(page_identifier="screenrank"):
    """
    Fetches raw HTML for a Facebook public page using TLS/JA3 browser impersonation.
    """
    if "facebook.com" in page_identifier:
        clean_url = page_identifier.strip()
    else:
        clean_name = page_identifier.strip().lstrip("@/")
        clean_url = f"https://www.facebook.com/{clean_name}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }

    response = requests.get(
        clean_url,
        headers=headers,
        impersonate="chrome120",
        timeout=25
    )

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch Facebook page (HTTP {response.status_code}): {clean_url}")

    return response.text, clean_url

def parse_facebook_page(html, target_url="https://www.facebook.com/screenrank"):
    """
    Parses Facebook Comet / Relay GraphQL JSON payloads from HTML to extract posts.
    """
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.string.strip() if soup.title and soup.title.string else "Screen Rank"
    if " | Facebook" in page_title:
        page_title = page_title.replace(" | Facebook", "").strip()

    scripts = soup.find_all("script", type="application/json")
    posts_found = []

    def extract_node_data(node):
        if not isinstance(node, dict):
            return None

        post_id = node.get("post_id")
        creation_time = node.get("creation_time")
        comet = node.get("comet_sections", {})
        content = comet.get("content", {})
        story = content.get("story", {})

        # Message Extraction
        message_obj = story.get("message")
        if not message_obj:
            message_obj = comet.get("message_container", {}).get("story", {}).get("message")
        
        full_text = ""
        if isinstance(message_obj, dict):
            full_text = message_obj.get("text", "") or ""

        # Post Permalink URL
        post_url = None
        context_layout = comet.get("context_layout", {}).get("story", {}).get("comet_sections", {})
        metadata_list = context_layout.get("metadata", [])
        for m in metadata_list:
            m_story = m.get("story", {})
            if "url" in m_story:
                post_url = m_story["url"]
                break

        # Attachments / Photos
        images = []
        attachments = story.get("attachments", [])
        for att in attachments:
            media = att.get("styles", {}).get("attachment", {}).get("media", {})
            if media:
                for img_key in ["image", "large_share_image", "photo_image"]:
                    img_data = media.get(img_key)
                    if isinstance(img_data, dict) and img_data.get("uri"):
                        images.append(img_data["uri"])

        # Feedback / Reactions / Comments / Shares
        feedback_obj = story.get("feedback", {})
        reaction_count = 0
        comment_count = 0
        share_count = 0

        if isinstance(feedback_obj, dict):
            # Reaction count
            rc = feedback_obj.get("reaction_count")
            if isinstance(rc, dict):
                reaction_count = rc.get("count", 0) or 0
            elif isinstance(rc, int):
                reaction_count = rc

            # Comment count
            cri = feedback_obj.get("comment_rendering_instance")
            if isinstance(cri, dict):
                comment_count = cri.get("comments", {}).get("total_count", 0) or 0
            elif isinstance(feedback_obj.get("total_comment_count"), int):
                comment_count = feedback_obj.get("total_comment_count")

            # Share count
            sc = feedback_obj.get("share_count")
            if isinstance(sc, dict):
                share_count = sc.get("count", 0) or 0
            elif isinstance(sc, int):
                share_count = sc

        if post_id or full_text:
            return {
                "post_id": str(post_id) if post_id else None,
                "creation_time": creation_time,
                "post_url": post_url or (f"https://www.facebook.com/{post_id}" if post_id else target_url),
                "full_text": full_text.strip(),
                "images": list(dict.fromkeys(images)),
                "reactions_count": reaction_count,
                "comments_count": comment_count,
                "shares_count": share_count
            }
        return None

    def scan_tree(obj):
        if isinstance(obj, dict):
            if "timeline_list_feed_units" in obj:
                edges = obj["timeline_list_feed_units"].get("edges", [])
                for e in edges:
                    p = extract_node_data(e.get("node", {}))
                    if p:
                        posts_found.append(p)

            for k, v in obj.items():
                scan_tree(v)
        elif isinstance(obj, list):
            for item in obj:
                scan_tree(item)

    for s in scripts:
        if not s.string:
            continue
        try:
            data = json.loads(s.string)
            scan_tree(data)
        except Exception:
            continue

    # Fallback to OpenGraph / Meta tags if JSON structures fail
    if not posts_found:
        og_desc = soup.find("meta", property="og:description")
        og_image = soup.find("meta", property="og:image")
        desc = og_desc["content"] if og_desc and og_desc.get("content") else ""
        img = og_image["content"] if og_image and og_image.get("content") else None
        if desc:
            posts_found.append({
                "post_id": "meta_extracted",
                "creation_time": int(datetime.now(timezone.utc).timestamp()),
                "post_url": target_url,
                "full_text": desc,
                "images": [img] if img else [],
                "reactions_count": 0,
                "comments_count": 0,
                "shares_count": 0
            })

    unique_posts = []
    seen_ids = set()
    for p in posts_found:
        pid = p["post_id"] or p["full_text"][:50]
        if pid and pid not in seen_ids:
            seen_ids.add(pid)
            unique_posts.append(p)

    unique_posts.sort(key=lambda x: x["creation_time"] or 0, reverse=True)

    if not unique_posts:
        raise ValueError(f"No posts could be extracted from {target_url}. Check connection or page privacy.")

    latest = unique_posts[0]

    raw_lines = [line.strip() for line in latest["full_text"].split("\n") if line.strip()]
    if raw_lines:
        headline = raw_lines[0]
        summary = " ".join(raw_lines[1:]) if len(raw_lines) > 1 else headline
    else:
        headline = "New post from " + page_title
        summary = headline

    dt_obj = datetime.fromtimestamp(latest["creation_time"], tz=timezone.utc) if latest["creation_time"] else None

    return {
        "page_name": page_title,
        "page_url": target_url,
        "post_id": latest["post_id"],
        "post_url": latest["post_url"],
        "timestamp": latest["creation_time"],
        "datetime_utc": dt_obj.strftime("%Y-%m-%d %H:%M:%S UTC") if dt_obj else None,
        "time_ago": format_time_ago(latest["creation_time"]),
        "headline": headline,
        "summary": summary[:300] + ("..." if len(summary) > 300 else ""),
        "full_text": latest["full_text"],
        "image_url": latest["images"][0] if latest["images"] else None,
        "all_images": latest["images"],
        "reactions_count": latest["reactions_count"],
        "comments_count": latest["comments_count"],
        "shares_count": latest["shares_count"]
    }

def get_latest_post(page_identifier="screenrank", open_in_browser=False):
    """
    Main entry point: fetches the Facebook page and returns the latest post data dict.
    Optionally opens the page in the browser if open_in_browser=True.
    """
    html, target_url = fetch_facebook_html(page_identifier)
    if open_in_browser:
        try:
            webbrowser.open(target_url)
        except Exception:
            pass
    return parse_facebook_page(html, target_url)

def check_for_new_post(page_identifier="screenrank", cache_path=CACHE_FILE):
    """
    Fetches latest post and checks if it is new compared to the cached last-seen post.
    Updates the cache file if a new post is detected.
    Returns: (is_new: bool, post_data: dict)
    """
    post = get_latest_post(page_identifier)
    last_id = None

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
                last_id = cached.get("post_id")
        except Exception:
            last_id = None

    is_new = (post.get("post_id") != last_id) if last_id else True

    # Update cache
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(post, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return is_new, post

def download_image(url, destination_filename="facebook_latest.jpg"):
    """
    Helper to download the high-resolution image attached to the post.
    Saves in the script's directory by default.
    """
    if not url:
        raise ValueError("No image URL provided.")

    if not os.path.isabs(destination_filename):
        destination_filename = os.path.join(SCRIPT_DIR, destination_filename)

    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=25)
    if r.status_code == 200:
        with open(destination_filename, "wb") as f:
            f.write(r.content)
        return destination_filename
    raise RuntimeError(f"Failed to download image (HTTP {r.status_code})")

if __name__ == "__main__":
    args = sys.argv[1:]
    target = "screenrank"
    open_browser = False
    output_json = False
    download_img = False
    save_file = None
    check_new = False

    for arg in args:
        if arg == "--open":
            open_browser = True
        elif arg == "--json":
            output_json = True
        elif arg == "--download-img":
            download_img = True
        elif arg == "--check-new":
            check_new = True
        elif arg.startswith("--save="):
            save_file = arg.split("=", 1)[1]
        elif not arg.startswith("--"):
            target = arg

    print(f"\n[+] Connecting to Facebook page: {target} ...")
    if open_browser:
        print("[+] Opening page in your web browser...")

    try:
        if check_new:
            is_new, data = check_for_new_post(target)
            print(f"[*] New post detected: {is_new}")
        else:
            data = get_latest_post(target, open_in_browser=open_browser)

        if output_json:
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            print(json_str)
            if save_file:
                with open(save_file, "w", encoding="utf-8") as f:
                    f.write(json_str)
                print(f"[✓] Saved JSON data to {save_file}")
        else:
            print("=" * 65)
            print(f" Page Name:       {data['page_name']}")
            print(f" Page URL:        {data['page_url']}")
            print(f" Post ID:         {data['post_id']}")
            print(f" Published:       {data['datetime_utc']} ({data['time_ago']})")
            print(f" Post URL:        {data['post_url']}")
            print(f" Engagement:      👍 {data['reactions_count']} reactions | 💬 {data['comments_count']} comments | 🔁 {data['shares_count']} shares")
            print("-" * 65)
            print(f" Headline:\n {data['headline']}")
            print("-" * 65)
            print(f" Full Message:\n{data['full_text']}")
            print("-" * 65)
            print(f" Image Attached:  {data['image_url'] or 'None'}")
            print("=" * 65)

        if download_img and data.get("image_url"):
            dest = download_image(data["image_url"], "screenrank_latest.jpg")
            print(f"\n[✓] High-res image saved to: {dest}")

    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)
