from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

# কুকি ফাইলের নাম
COOKIE_FILE = 'cookies.txt'

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url') if data else None
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # yt-dlp কনফিগারেশন - এখানে কুকি ফাইলটি যুক্ত করা হয়েছে
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    
    # যদি cookies.txt ফাইলটি ফোল্ডারে থাকে, তবে সেটি ব্যবহার করবে
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # ভিডিওর লিঙ্ক বের করার চেষ্টা
            video_url = info.get('url')
            if not video_url:
                formats = info.get('formats', [])
                # ভালো কোয়ালিটির MP4 ফরম্যাট খোঁজা
                for f in formats:
                    if f.get('ext') == 'mp4' and f.get('url'):
                        video_url = f.get('url')
                        break
            
            if not video_url:
                return jsonify({'error': 'No suitable media URL found'}), 404
                
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'url': video_url
            })
    
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({'error': 'Failed to fetch. The video might be private or restricted.'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
