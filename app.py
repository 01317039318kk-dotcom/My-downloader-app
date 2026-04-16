from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import requests

app = Flask(__name__)
DOWNLOAD_FOLDER = '/tmp'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', 'Bangla hit songs')
    page_token = request.args.get('pageToken', '')
    api_key = os.environ.get("YOUTUBE_API_KEY")
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
    except:
        return jsonify({"videos": [], "nextPageToken": ""})

@app.route('/get_info', methods=['POST'])
def get_info():
    video_url = request.form.get('url')
    # সিকিউরিটি এবং এরর এড়াতে নতুন অপশন
    ydl_opts = {'quiet': True, 'no_warnings': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            # সরাসরি MP4 ফরম্যাট খুঁজো
            formats = info.get('formats', [])
            # অডিও-ভিডিও যুক্ত স্ট্রিম খুঁজে বের করা
            stream = next((f for f in formats if f.get('ext') == 'mp4' and f.get('vcodec') != 'none' and f.get('acodec') != 'none'), info)
            return jsonify({"title": info.get('title'), "video_url": stream.get('url'), "url": video_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download')
def download():
    video_url = request.args.get('url')
    # FFmpeg ছাড়াই ডাউনলোড সম্ভব এমন ফরম্যাট ব্যবহার করা
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
    
