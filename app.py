from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import requests

app = Flask(__name__)

# Render-এর জন্য টেম্পোরারি ফোল্ডার ব্যবহার করা
DOWNLOAD_FOLDER = '/tmp'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', 'Bangla hit songs')
    page_token = request.args.get('pageToken', '')
    api_key = os.environ.get("YOUTUBE_API_KEY") # Render Settings থেকে সেট করুন
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults=12&q={query}&type=video&pageToken={page_token}&key={api_key}"
    try:
        r = requests.get(url).json()
        videos = []
        for item in r.get('items', []):
            videos.append({
                "title": item['snippet']['title'],
                "thumbnail": item['snippet']['thumbnails']['high']['url'],
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
            })
        return jsonify({"videos": videos, "nextPageToken": r.get('nextPageToken', '')})
    except Exception as e:
        return jsonify({"error": str(e), "videos": []})

@app.route('/get_info', methods=['POST'])
def get_info():
    video_url = request.form.get('url')
    # yt-dlp অপশন আপডেট (সার্ভারের জন্য হালকা)
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            # সরাসরি স্ট্রিম লিঙ্ক বের করা
            formats = info.get('formats', [])
            # ভিডিও ফরম্যাট খুঁজে বের করা
            video_stream = next((f for f in formats if f.get('ext') == 'mp4' and f.get('vcodec') != 'none'), None)
            play_url = video_stream['url'] if video_stream else info.get('url')
            
            return jsonify({"title": info['title'], "video_url": play_url, "url": video_url})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    video_url = request.args.get('url')
    # ডাউনলোড করার সময় FFmpeg এর সমস্যা এড়াতে শুধু mp4 ফরম্যাট সিলেক্ট করা
    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        filename = ydl.prepare_filename(info)
        return send_file(filename, as_attachment=True)

@app.route('/get_downloads')
def get_downloads():
    files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.endswith('.mp4')]
    return jsonify(files)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
            
