from flask import Flask, request, jsonify, render_template
import yt_dlp
import os

app = Flask(__name__)

# কুকি ফাইল অবশ্যই প্রজেক্টের মেইন ডিরেক্টরিতে থাকতে হবে
COOKIE_FILE = 'cookies.txt'

@app.route('/')
def home():
    # এটি আপনার templates/index.html ফাইলটি লোড করবে
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    data = request.get_json()
    url = data.get('url') if data else None
    
    if not url:
        return jsonify({'error': 'URL প্রদান করা হয়নি'}), 400

    # yt-dlp এর জন্য কনফিগারেশন
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        # বট ডিটেকশন এড়াতে ব্রাউজার ইউজার এজেন্ট ব্যবহার করা হয়েছে
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
    
    # কুকি ফাইল থাকলে তা লোড করা হচ্ছে
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE
    else:
        print("সতর্কবার্তা: cookies.txt ফাইলটি পাওয়া যায়নি!")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ভিডিওর তথ্য সংগ্রহ
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি ভিডিও URL পাওয়ার চেষ্টা
            video_url = info.get('url')
            
            # যদি URL না পাওয়া যায়, ফরম্যাট লিস্ট চেক করা
            if not video_url:
                formats = info.get('formats', [])
                for f in formats:
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                        video_url = f.get('url')
                        break
            
            if not video_url:
                return jsonify({'error': 'ভিডিও লিঙ্ক খুঁজে পাওয়া যায়নি!'}), 404
                
            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'url': video_url
            })
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error occurred: {error_msg}")
        return jsonify({'error': 'তথ্য সংগ্রহ করতে ব্যর্থ হয়েছে', 'details': error_msg}), 500

if __name__ == '__main__':
    # রেন্ডারের জন্য পোর্ট সেটআপ
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
