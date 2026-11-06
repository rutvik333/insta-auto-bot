import os
import re
import sys
import urllib.parse
import numpy as np
from PIL import Image

try:
    from curl_cffi import requests
except ImportError:
    import requests

try:
    import cv2
except ImportError:
    cv2 = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def inpaint_remove_text_and_logo(input_image_path, output_image_path=None, sensitivity="medium"):
    """
    Detects and erases logos, watermarks, text overlays, and subtitles
    using morphological gradient masking and OpenCV Telea inpainting.
    """
    if cv2 is None:
        raise RuntimeError("opencv-python is required for inpainting. Run: pip install opencv-python")

    if not os.path.isabs(input_image_path):
        input_image_path = os.path.join(SCRIPT_DIR, input_image_path)

    if not os.path.exists(input_image_path):
        raise FileNotFoundError(f"Input image not found: {input_image_path}")

    if not output_image_path:
        output_image_path = os.path.join(SCRIPT_DIR, "clean_image.jpg")
    elif not os.path.isabs(output_image_path):
        output_image_path = os.path.join(SCRIPT_DIR, output_image_path)

    img = cv2.imread(input_image_path)
    if img is None:
        raise ValueError(f"Could not load image: {input_image_path}")

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Morphological Gradient to capture high-contrast text and logo edges
    if sensitivity == "high":
        k_w, k_h = 19, 5
        iterations = 2
    elif sensitivity == "low":
        k_w, k_h = 11, 3
        iterations = 1
    else:  # medium
        k_w, k_h = 15, 4
        iterations = 1

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_w, k_h))
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)

    # 2. Adaptive threshold
    thresh = cv2.adaptiveThreshold(
        grad, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2
    )

    # 3. Canny edges for sharp vector logos/badges
    edges = cv2.Canny(gray, 70, 180)
    combined = cv2.bitwise_or(thresh, edges)

    # 4. Contour filtering: only mask regions that resemble text lines or watermark boxes
    contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros((h, w), dtype=np.uint8)

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        aspect = cw / float(ch + 1e-5)
        area = cw * ch

        # Skip giant areas (> 45% of entire photo) or single-pixel dots
        if 15 < area < (h * w * 0.45):
            is_corner_logo = (x < w * 0.25 or x + cw > w * 0.75) and (y < h * 0.25 or y + ch > h * 0.75)
            # Text has horizontal aspect ratio or is in typical banner areas
            if aspect > 0.4 or is_corner_logo or area < 2000:
                cv2.drawContours(mask, [c], -1, 255, -1)

    # 5. Dilate mask slightly to prevent halos
    dilate_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, dilate_kernel, iterations=iterations)

    # 6. High quality Telea inpainting
    cleaned = cv2.inpaint(img, mask, inpaintRadius=4, flags=cv2.INPAINT_TELEA)

    cv2.imwrite(output_image_path, cleaned, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return output_image_path

def fetch_clean_source_image(headline_or_query, output_image_path=None):
    """
    Searches and downloads the original high-resolution studio photo / movie still
    free of any Facebook overlays, logos, or captions.
    """
    if not output_image_path:
        output_image_path = os.path.join(SCRIPT_DIR, "clean_source.jpg")
    elif not os.path.isabs(output_image_path):
        output_image_path = os.path.join(SCRIPT_DIR, output_image_path)

    # Clean query from emojis and punctuation
    clean_q = re.sub(r'[\U00010000-\U0010ffff]', '', headline_or_query)
    clean_q = re.sub(r'[‘\'"“”\n\r!?:;]', ' ', clean_q)
    words = [w for w in clean_q.split() if len(w) > 2]
    query_str = " ".join(words[:5]).strip()

    print(f"[+] Searching clean studio master image for: '{query_str}' ...")
    search_url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query_str)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(search_url, headers=headers, impersonate="chrome120", timeout=12)
    except Exception:
        resp = requests.get(search_url, headers=headers, timeout=12)

    urls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', resp.text)

    if not urls:
        raise RuntimeError(f"No clean source images found for: {query_str}")

    for candidate_url in urls[:6]:
        try:
            img_resp = requests.get(candidate_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if img_resp.status_code == 200 and len(img_resp.content) > 10000:
                with open(output_image_path, "wb") as f:
                    f.write(img_resp.content)
                im = Image.open(output_image_path)
                if im.width >= 350 and im.height >= 350:
                    return output_image_path
        except Exception:
            continue

    raise RuntimeError("Could not download a valid clean image candidate.")

def clean_post_image(input_image_path=None, headline="", mode="inpaint", output_path=None):
    """
    Unified entry point for image cleaning:
    - mode="inpaint": Inpaints out watermarks and text from the downloaded Facebook photo.
    - mode="clean_source": Finds pristine, text-free original studio still.
    """
    if mode == "clean_source":
        if not headline and input_image_path:
            headline = os.path.basename(input_image_path)
        return fetch_clean_source_image(headline, output_path)
    else:
        if not input_image_path:
            input_image_path = os.path.join(SCRIPT_DIR, "screenrank_latest.jpg")
        return inpaint_remove_text_and_logo(input_image_path, output_path)

if __name__ == "__main__":
    args = sys.argv[1:]
    mode = "inpaint"
    src = os.path.join(SCRIPT_DIR, "screenrank_latest.jpg")
    query = "Screen Rank update"

    for arg in args:
        if arg == "--clean-source":
            mode = "clean_source"
        elif arg.startswith("--query="):
            query = arg.split("=", 1)[1]
        elif not arg.startswith("--"):
            src = arg

    print(f"\n[+] Cleaning image: {src} (Mode: {mode}) ...")
    try:
        out = clean_post_image(src, headline=query, mode=mode)
        print(f"[✓] Success! Clean image saved to: {out}")
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)
