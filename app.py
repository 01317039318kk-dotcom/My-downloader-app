from flask import Flask, request, jsonify, render_template
import yt_dlp
import os

app = Flask(__name__)

# কুকি ফাইলের নাম (নিশ্চিত করুন এটি আপনার মেইন ফোল্ডারে আছে)
COOKIE_FILE = 'cookies.txt'

@app.route('/')
def home():
    # এটি আপনার templates/index.html ফাইলটি লোড করবে
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    try:
        data = request.get_json()
        url = data.get('url') if data else None
        
        if not url:
            return jsonify({'error': 'URL প্রদান করা হয়নি'}), 400

        # yt-dlp এর জন্য শক্তিশালী কনফিগারেশন
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            # আধুনিক ব্রাউজার হেডার যা বট ডিটেকশন এড়াতে সাহায্য করে
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'extract_flat': False,
        }
        
        # যদি cookies.txt ফাইলটি সার্ভারে থাকে তবেই সেটি ব্যবহার করবে
        if os.path.exists(COOKIE_FILE):
            ydl_opts['cookiefile'] = COOKIE_FILE
        else:
            print("সতর্কবার্তা: cookies.txt ফাইলটি পাওয়া যায়নি!")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ভিডিওর তথ্য সংগ্রহ
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি ভিডিও URL পাওয়ার চেষ্টা
            video_url = info.get('url')
            
            # যদি সরাসরি URL না পাওয়া যায়, তবে ফরম্যাট লিস্ট থেকে খুঁজে বের করা
            if not video_url:
                formats = info.get('formats', [])
                for f in formats:
                    # mp4 ফরম্যাট এবং যেখানে অডিও-ভিডিও দুইটাই আছে এমন লিঙ্ক খোঁজা
                    if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('ext') == 'mp4':
                        video_url = f.get('url')
                        break
            
            if not video_url:
                return jsonify({'error': 'উপযুক্ত ভিডিও লিঙ্ক খুঁজে পাওয়া যায়নি'}), 404
                
            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'url': video_url,
                'duration': info.get('duration')
            })
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error occurred: {error_msg}")
        # ইউটিউব যদি সাইন-ইন করতে বলে তবে ব্যবহারকারীকে স্পষ্ট মেসেজ দিবে
        if "confirm you're not a bot" in error_msg.lower():
            return jsonify({'error': 'ইউটিউব বট হিসেবে শনাক্ত করেছে। দয়া করে cookies.txt আপডেট করুন।'}), 403
        return jsonify({'error': 'তথ্য সংগ্রহ করতে ব্যর্থ হয়েছে', 'details': error_msg}), 500

if __name__ == '__main__':
    # রেন্ডারে পোর্ট এনভায়রনমেন্ট ভেরিয়েবল অনুযায়ী সেট হবে
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
