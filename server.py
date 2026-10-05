from flask import Flask, request, render_template_string, send_file
import os
import main  # Import the bot script directly!

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Insta Auto Bot</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen font-sans p-8 flex justify-center items-start">

    <div class="bg-white rounded-xl shadow-lg p-8 max-w-2xl w-full">
        <h1 class="text-3xl font-bold text-gray-900 mb-6 text-center">Insta Auto Bot</h1>
        
        {% if error %}
        <div class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg font-bold">{{ error }}</div>
        {% endif %}

        {% if success %}
        <div class="mb-4 p-4 bg-green-100 text-green-700 rounded-lg font-bold text-xl text-center">{{ success }}</div>
        {% endif %}

        <!-- STEP 1: GENERATE PREVIEW -->
        <div class="border-b pb-6 mb-6">
            <h2 class="text-xl font-bold mb-4 text-gray-800">Step 1: Generate Preview</h2>
            <p class="text-sm text-gray-500 mb-4">Fetch the latest trending news and generate an image. This does not post to Instagram yet.</p>
            <form method="POST" action="/preview">
                <button type="submit" onclick="this.innerText='Generating... Please wait (approx 10s)';" class="w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700 transition">
                    Fetch News & Generate Image Preview
                </button>
            </form>
        </div>

        <!-- STEP 2: REVIEW AND PUBLISH -->
        {% if has_preview %}
        <div class="bg-blue-50 border border-blue-100 p-6 rounded-lg shadow-inner">
            <h2 class="text-xl font-bold mb-4 text-blue-900">Step 2: Review & Publish</h2>
            
            <div class="mb-6 flex flex-col items-center">
                <h3 class="font-bold text-gray-800 mb-2 w-full text-left">Caption that will be posted:</h3>
                <div class="bg-white p-4 rounded border w-full text-sm whitespace-pre-wrap text-gray-700 mb-4">{{ caption }}</div>
                
                <h3 class="font-bold text-gray-800 mb-2 w-full text-left">Image that will be posted:</h3>
                <img src="/image?t={{ time }}" class="rounded shadow-md max-w-sm border w-full">
            </div>

            <form method="POST" action="/publish" class="space-y-4 bg-white p-6 rounded-lg border shadow-sm">
                <h3 class="font-bold text-gray-800 border-b pb-2">Final Approval</h3>
                <input type="hidden" name="headline" value="{{ headline }}">
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-1">Instagram Username</label>
                    <input type="text" name="user" required class="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-sm font-bold text-gray-700 mb-1">Instagram Password</label>
                    <input type="password" name="pass" required class="w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500">
                </div>
                <button type="submit" onclick="this.innerText='Publishing to Instagram... Please wait';" class="w-full bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 transition shadow-lg text-lg">
                    Approve & Publish to Instagram
                </button>
            </form>
        </div>
        {% endif %}
    </div>

</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/preview", methods=["POST"])
def preview():
    try:
        headline, subhead = main.fetch_trending_news()
        raw_img = main.fetch_relevant_image(headline)
        final_img = main.format_image_for_instagram(raw_img, headline, subhead)
        
        caption = f"🚨 BREAKING NEWS 🚨\n\n{headline}\n\n#news #entertainment #marvel #hollywood #trending"
        
        import time
        return render_template_string(HTML, has_preview=True, caption=caption, headline=headline, time=time.time())
    except Exception as e:
        return render_template_string(HTML, error=str(e))

@app.route("/publish", methods=["POST"])
def publish():
    u = request.form.get("user")
    p = request.form.get("pass")
    headline = request.form.get("headline")
    
    os.environ["IG_USERNAME"] = u
    os.environ["IG_PASSWORD"] = p
    
    try:
        main.post_to_instagram("post.jpg", headline)
        return render_template_string(HTML, success="✅ Successfully Published to Instagram!")
    except Exception as e:
        return render_template_string(HTML, error="Failed to post: " + str(e))

@app.route("/image")
def get_image():
    if os.path.exists("post.jpg"):
        return send_file("post.jpg", mimetype='image/jpeg')
    return "No image found", 404

if __name__ == "__main__":
    print("=========================================")
    print("LOCAL SERVER RUNNING!")
    print("Open this link in your browser: http://127.0.0.1:5000")
    print("=========================================")
    app.run(port=5000)
