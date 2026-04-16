from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import requests

app = Flask(__name__)
# Render-এর জন্য টেম্পোরারি ফোল্ডার
DOWNLOAD_FOLDER = '/tmp'
# কুকি ফাইলের সঠিক পাথ সেট করা
COOKIE_PATH = os.path.join(os.getcwd(), 'cookies.txt')

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
    # উন্নত ydl_opts কনফিগারেশন
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'cookiefile': COOKIE_PATH,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            play_url = info.get('url')
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                        play_url = f.get('url')
                        break
            
            return jsonify({"title": info.get('title'), "video_url": play_url, "url": video_url})
    except Exception as e:
        return jsonify({"error": f"লিঙ্কটি পাওয়া যায়নি: {str(e)}"}), 500

@app.route('/download')
def download():
    video_url = request.args.get('url')
    ydl_opts = {
        'format': 'best', 
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'cookiefile': COOKIE_PATH,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"ডাউনলোড ব্যর্থ হয়েছে: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
