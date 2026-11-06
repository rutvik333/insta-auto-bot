import os
import time
import webbrowser
from flask import Flask, request, render_template_string, send_file, redirect, url_for
import main
import facebook_scraper
import image_cleaner

app = Flask(__name__)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insta Auto Bot | Facebook & Instagram Automation</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen font-sans p-4 sm:p-8">

    <div class="max-w-4xl mx-auto space-y-6">
        <!-- Header -->
        <header class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-tr from-pink-500 via-purple-500 to-indigo-500 flex items-center justify-center text-white shadow-lg text-2xl">
                    <i class="fa-brands fa-instagram"></i>
                </div>
                <div>
                    <h1 class="text-2xl font-black tracking-tight text-white flex items-center gap-2">
                        Insta Auto Bot
                        <span class="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">v2.0 Screen Rank</span>
                    </h1>
                    <p class="text-xs text-slate-400">Automated Content Extraction & Instagram Publishing Tool</p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <a href="https://github.com/rutvik333/insta-auto-bot" target="_blank" class="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold rounded-lg transition flex items-center gap-2 border border-slate-600">
                    <i class="fa-brands fa-github text-sm"></i> GitHub Repo
                </a>
            </div>
        </header>

        {% if error %}
        <div class="p-4 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl flex items-center gap-3 text-sm">
            <i class="fa-solid fa-triangle-exclamation text-rose-400 text-lg"></i>
            <div><strong>Error:</strong> {{ error }}</div>
        </div>
        {% endif %}

        {% if success %}
        <div class="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 rounded-xl flex items-center gap-3 text-sm">
            <i class="fa-solid fa-circle-check text-emerald-400 text-lg"></i>
            <div>{{ success }}</div>
        </div>
        {% endif %}

        <!-- STEP 1: FACEBOOK DATA EXTRACTOR -->
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl">
            <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                    <span class="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center text-xs font-bold">1</span>
                    <h2 class="text-lg font-bold text-white flex items-center gap-2">
                        <i class="fa-brands fa-facebook text-blue-500"></i>
                        Screen Rank Facebook Automation
                    </h2>
                </div>
                <div class="flex items-center gap-2">
                    <form method="POST" action="/open_facebook" target="_blank">
                        <button type="submit" class="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-xs text-slate-300 font-medium rounded-lg transition flex items-center gap-1.5 border border-slate-600">
                            <i class="fa-solid fa-arrow-up-right-from-square"></i> Open Facebook Page
                        </button>
                    </form>
                </div>
            </div>

            <p class="text-sm text-slate-400 mb-5">
                Target: <a href="https://www.facebook.com/screenrank" target="_blank" class="text-blue-400 hover:underline font-mono">https://www.facebook.com/screenrank</a>. Click below to inspect the latest live post data.
            </p>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                <form method="POST" action="/fetch_facebook">
                    <button type="submit" onclick="this.innerHTML='<i class=\\'fa-solid fa-spinner fa-spin\\'></i> Connecting to Facebook...';" class="w-full bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-blue-600/20 text-sm">
                        <i class="fa-brands fa-facebook-f"></i> Fetch Latest Facebook Post Data
                    </button>
                </form>

                <form method="POST" action="/preview_rss">
                    <button type="submit" onclick="this.innerHTML='<i class=\\'fa-solid fa-spinner fa-spin\\'></i> Searching Google News...';" class="w-full bg-slate-700 hover:bg-slate-600 text-slate-200 py-3 rounded-xl font-bold transition flex items-center justify-center gap-2 text-sm border border-slate-600">
                        <i class="fa-solid fa-newspaper text-slate-400"></i> Fallback: Google News RSS
                    </button>
                </form>
            </div>

            <!-- FB POST DATA CARD -->
            {% if fb_data %}
            <div class="bg-slate-900/80 border border-slate-700 rounded-xl p-5 space-y-4">
                <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Latest Live Post</span>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">{{ fb_data.time_ago }}</span>
                    </div>
                    <div class="flex items-center gap-3 text-xs text-slate-400">
                        <span><i class="fa-solid fa-calendar-day text-slate-500 mr-1"></i>{{ fb_data.datetime_utc }}</span>
                        <a href="{{ fb_data.post_url }}" target="_blank" class="text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1">
                            View on FB <i class="fa-solid fa-up-right-from-square text-[10px]"></i>
                        </a>
                    </div>
                </div>

                <div class="space-y-2">
                    <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Headline:</div>
                    <div class="text-base font-bold text-white bg-slate-800/60 p-3 rounded-lg border border-slate-700/60">
                        {{ fb_data.headline }}
                    </div>
                </div>

                <div class="space-y-2">
                    <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Post Message:</div>
                    <div class="text-xs sm:text-sm text-slate-300 bg-slate-800/40 p-3 rounded-lg border border-slate-700/40 whitespace-pre-line leading-relaxed max-h-40 overflow-y-auto">
                        {{ fb_data.full_text }}
                    </div>
                </div>

                <div class="flex flex-wrap items-center justify-between gap-4 pt-2">
                    <div class="flex items-center gap-4 text-xs font-semibold text-slate-400">
                        <span class="flex items-center gap-1.5"><i class="fa-solid fa-thumbs-up text-blue-400"></i> {{ fb_data.reactions_count }} Reactions</span>
                        <span class="flex items-center gap-1.5"><i class="fa-solid fa-comment text-emerald-400"></i> {{ fb_data.comments_count }} Comments</span>
                        <span class="flex items-center gap-1.5"><i class="fa-solid fa-share text-purple-400"></i> {{ fb_data.shares_count }} Shares</span>
                    </div>

                    <form method="POST" action="/preview_fb">
                        <input type="hidden" name="headline" value="{{ fb_data.headline }}">
                        <input type="hidden" name="subhead" value="{{ fb_data.summary }}">
                        <input type="hidden" name="img_url" value="{{ fb_data.image_url or '' }}">
                        <input type="hidden" name="post_url" value="{{ fb_data.post_url }}">
                        <input type="hidden" name="full_text" value="{{ fb_data.full_text }}">
                        <button type="submit" onclick="this.innerHTML='<i class=\\'fa-solid fa-spinner fa-spin\\'></i> Generating Graphic...';" class="px-5 py-2.5 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white rounded-lg font-bold text-xs sm:text-sm transition shadow-lg shadow-pink-600/20 flex items-center gap-2">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> Generate Instagram Post from this Update
                        </button>
                    </form>
                </div>
            </div>
            {% endif %}
        </div>

        <!-- STEP 2: REVIEW & APPROVE INSTAGRAM POST -->
        {% if has_preview %}
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 shadow-xl space-y-6">
            <div class="flex items-center gap-2">
                <span class="w-7 h-7 rounded-lg bg-pink-600 text-white flex items-center justify-center text-xs font-bold">2</span>
                <h2 class="text-lg font-bold text-white flex items-center gap-2">
                    <i class="fa-brands fa-instagram text-pink-500"></i>
                    Review & Publish to Instagram
                </h2>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                <!-- Preview Image -->
                <div class="space-y-2">
                    <div class="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                        <span>Generated 4:5 Portrait Graphic:</span>
                        <a href="/image?t={{ time }}" target="_blank" class="text-blue-400 text-[11px] hover:underline">Full Res</a>
                    </div>
                    <div class="bg-black rounded-xl overflow-hidden border border-slate-700 shadow-2xl flex items-center justify-center p-1">
                        <img src="/image?t={{ time }}" class="rounded-lg max-h-[480px] w-auto object-contain mx-auto shadow">
                    </div>
                </div>

                <!-- Approval Form -->
                <form method="POST" action="/publish" class="space-y-4 bg-slate-900/80 p-5 rounded-xl border border-slate-700">
                    <h3 class="text-sm font-bold text-slate-200 border-b border-slate-800 pb-2 flex items-center gap-2">
                        <i class="fa-solid fa-shield-halved text-emerald-400"></i> Ready to Publish
                    </h3>

                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Caption</label>
                        <textarea name="caption" rows="6" class="w-full bg-slate-800 text-slate-200 text-xs sm:text-sm p-3 border border-slate-700 rounded-lg focus:ring-2 focus:ring-pink-500 focus:outline-none font-sans leading-relaxed">{{ caption }}</textarea>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Instagram Username</label>
                            <input type="text" name="user" required placeholder="username" value="{{ ig_user or '' }}" class="w-full bg-slate-800 text-slate-200 text-xs sm:text-sm p-2.5 border border-slate-700 rounded-lg focus:ring-2 focus:ring-pink-500 focus:outline-none">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Instagram Password</label>
                            <input type="password" name="pass" required placeholder="••••••••" class="w-full bg-slate-800 text-slate-200 text-xs sm:text-sm p-2.5 border border-slate-700 rounded-lg focus:ring-2 focus:ring-pink-500 focus:outline-none">
                        </div>
                    </div>

                    <button type="submit" onclick="this.innerHTML='<i class=\\'fa-solid fa-spinner fa-spin\\'></i> Publishing to Instagram...';" class="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white py-3 rounded-xl font-bold transition shadow-lg shadow-emerald-600/20 text-sm flex items-center justify-center gap-2">
                        <i class="fa-solid fa-paper-plane"></i> Approve & Publish to Instagram
                    </button>
                </form>
            </div>
        </div>
        {% endif %}
    </div>

</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/trigger", methods=["GET"])
def trigger_page():
    trigger_path = os.path.join(SCRIPT_DIR, "index.html")
    if os.path.exists(trigger_path):
        return send_file(trigger_path)
    return "Trigger page not found", 404

@app.route("/latest_data.json", methods=["GET"])
def latest_data_json():
    data_path = os.path.join(SCRIPT_DIR, "latest_data.json")
    if os.path.exists(data_path):
        return send_file(data_path, mimetype="application/json")
    return "{}", 404

@app.route("/clean_image", methods=["POST"])
def clean_image_api():
    try:
        data = request.get_json(silent=True) or request.form
        mode = data.get("mode", "inpaint")
        headline = data.get("headline", "")
        img_url = data.get("image_url", "")
        
        src_path = os.path.join(SCRIPT_DIR, "screenrank_latest.jpg")
        if (not os.path.exists(src_path) or os.path.getsize(src_path) < 1000) and img_url:
            facebook_scraper.download_image(img_url, src_path)

        out_name = "clean_image.jpg" if mode == "inpaint" else "clean_source.jpg"
        out_path = os.path.join(SCRIPT_DIR, out_name)
        
        image_cleaner.clean_post_image(src_path, headline=headline, mode=mode, output_path=out_path)
        
        return {
            "status": "success",
            "mode": mode,
            "clean_url": f"/{out_name}?t={time.time()}",
            "filename": out_name
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/clean_image.jpg")
def serve_clean_image():
    p = os.path.join(SCRIPT_DIR, "clean_image.jpg")
    if os.path.exists(p):
        return send_file(p, mimetype="image/jpeg")
    return "No clean image found", 404

@app.route("/clean_source.jpg")
def serve_clean_source():
    p = os.path.join(SCRIPT_DIR, "clean_source.jpg")
    if os.path.exists(p):
        return send_file(p, mimetype="image/jpeg")
    return "No clean source found", 404

@app.route("/open_facebook", methods=["POST", "GET"])
def open_fb():
    try:
        webbrowser.open("https://www.facebook.com/screenrank")
    except Exception:
        pass
    return redirect(url_for("index"))

@app.route("/fetch_facebook", methods=["POST", "GET"])
def fetch_fb():
    try:
        fb_data = facebook_scraper.get_latest_post("screenrank")
        return render_template_string(HTML, fb_data=fb_data)
    except Exception as e:
        return render_template_string(HTML, error=f"Facebook Extraction Error: {str(e)}")

@app.route("/preview_fb", methods=["POST"])
def preview_fb():
    try:
        headline = request.form.get("headline", "")
        subhead = request.form.get("subhead", "")
        img_url = request.form.get("img_url", "")
        post_url = request.form.get("post_url", "")
        full_text = request.form.get("full_text", "")

        raw_img = main.fetch_relevant_image(headline, direct_url=img_url if img_url else None)
        final_img = main.format_image_for_instagram(raw_img, headline, subhead)

        caption = f"🎬 {headline}\n\n{full_text}\n\nVia: Screen Rank ({post_url})\n\n#screenrank #movies #boxoffice #hollywood #cinema #entertainment"

        return render_template_string(
            HTML,
            has_preview=True,
            caption=caption,
            headline=headline,
            time=time.time(),
            ig_user=os.environ.get("IG_USERNAME", "")
        )
    except Exception as e:
        return render_template_string(HTML, error=f"Preview Generation Error: {str(e)}")

@app.route("/preview_rss", methods=["POST"])
def preview_rss():
    try:
        headline, subhead = main.fetch_trending_news()
        raw_img = main.fetch_relevant_image(headline)
        final_img = main.format_image_for_instagram(raw_img, headline, subhead)

        caption = f"🚨 BREAKING NEWS 🚨\n\n{headline}\n\n#news #entertainment #marvel #hollywood #trending"

        return render_template_string(
            HTML,
            has_preview=True,
            caption=caption,
            headline=headline,
            time=time.time(),
            ig_user=os.environ.get("IG_USERNAME", "")
        )
    except Exception as e:
        return render_template_string(HTML, error=f"Preview Generation Error: {str(e)}")

@app.route("/publish", methods=["POST"])
def publish():
    u = request.form.get("user")
    p = request.form.get("pass")
    caption = request.form.get("caption")

    os.environ["IG_USERNAME"] = u
    os.environ["IG_PASSWORD"] = p

    post_path = os.path.join(SCRIPT_DIR, "post.jpg")
    try:
        main.post_to_instagram(post_path, caption)
        return render_template_string(HTML, success="✅ Successfully Published to Instagram!")
    except Exception as e:
        return render_template_string(HTML, error="Failed to post: " + str(e))

@app.route("/image")
def get_image():
    post_path = os.path.join(SCRIPT_DIR, "post.jpg")
    if os.path.exists(post_path):
        return send_file(post_path, mimetype='image/jpeg')
    return "No image found", 404

if __name__ == "__main__":
    import socket
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print("=" * 60)
    print("🚀 INSTA AUTO BOT SERVER RUNNING!")
    print("👉 On this PC:     http://localhost:5000")
    print(f"👉 On your Mobile: http://{local_ip}:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
