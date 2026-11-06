# Insta Auto Bot 🤖 (Facebook Screen Rank Automation)

An automated social media engine connected to GitHub [rutvik333/insta-auto-bot](https://github.com/rutvik333/insta-auto-bot) that extracts the latest cinema, box office, and entertainment updates from the [Screen Rank Facebook page](https://www.facebook.com/screenrank), formats high-resolution graphics, and automates posting to Instagram.

---

## ⚡ Features

- **Live Facebook Data Extractor (`facebook_scraper.py`)**:
  - Connects to `https://www.facebook.com/screenrank` using browser impersonation (bypasses bot blocks).
  - Extracts the latest post's headline, full text caption, timestamp, post permalink, engagement (reactions, comments, shares), and high-resolution attached image.
  - Can optionally open the Facebook page directly in your default browser (`--open`).
- **Smart Image Formatter (`main.py`)**:
  - Automatically downloads the original Facebook post photo or searches relevant imagery.
  - Crops & scales to 4:5 Instagram portrait (1080x1350).
  - Applies a modern dark gradient and stylish typography overlay.
- **Interactive Web Dashboard (`server.py`)**:
  - Beautiful Tailwind CSS dark UI at `http://127.0.0.1:5000`.
  - 1-Click "Fetch Latest Facebook Post Data".
  - 1-Click "Open Facebook Page".
  - Preview generated graphics and live captions with approval flow.
- **GitHub Actions Scheduled Automation (`.github/workflows/schedule.yml`)**:
  - Runs twice daily (or manually triggered via GitHub Actions UI / `index.html`).

---

## 🚀 How to Use

### 1. Quick Facebook Scraping & Inspection

To inspect the latest post from `https://www.facebook.com/screenrank`:

```bash
# Print clean summary in terminal
python facebook_scraper.py

# Open the page in your browser while extracting data
python facebook_scraper.py --open

# Output raw JSON
python facebook_scraper.py --json

# Download the post's attached high-resolution image
python facebook_scraper.py --download-img
```

### 2. Run Full Generation (Image + Caption)

```bash
# Creates post.jpg and prepares the Instagram caption
python main.py
```

### 3. Launch Local Web Dashboard

```bash
python server.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser to view the interactive control panel.

---

## 📦 Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`:
  - `curl_cffi` (stealth browser requests)
  - `beautifulsoup4`
  - `Pillow`
  - `instagrapi`
  - `requests`
  - `feedparser`

Install with:
```bash
pip install -r requirements.txt
```

