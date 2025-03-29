from flask import Flask, request, send_file, jsonify
from pytubefix import YouTube
import os
import requests
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB

# 🔑 Replace with your YouTube API Key
YOUTUBE_API_KEY = "AIzaSyDKKLWJ4Xkc5PpFSb7dkiYIxGreHuyFx_k"

app = Flask(__name__)

def get_video_details(song_name):
    """Search YouTube for a video URL and get metadata (title, artist, album)."""
    search_url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": song_name,
        "key": YOUTUBE_API_KEY,
        "maxResults": 1,
        "type": "video"
    }

    response = requests.get(search_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            video_id = data["items"][0]["id"]["videoId"]
            title = data["items"][0]["snippet"]["title"]
            artist = data["items"][0]["snippet"]["channelTitle"]
            album = "YouTube Music"  # Default album name

            return {
                "video_url": f"https://www.youtube.com/watch?v={video_id}",
                "title": title,
                "artist": artist,
                "album": album
            }

    return None

def download_audio(video_url, song_title):
    """Download YouTube video as MP3."""
    try:
        yt = YouTube(video_url)
        print(f"📥 Downloading: {yt.title}")

        # Get best audio stream
        video = yt.streams.filter(only_audio=True).first()

        # Create downloads folder
        os.makedirs("downloads", exist_ok=True)

        # Download file
        out_file = video.download(output_path="downloads")

        # Convert to MP3
        base, ext = os.path.splitext(out_file)
        mp3_file = f"downloads/{song_title}.mp3"
        os.rename(out_file, mp3_file)

        print(f"✅ {yt.title} has been successfully downloaded as MP3!")
        return mp3_file
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def add_metadata(mp3_file, title, artist, album):
    """Add metadata (title, artist, album) to the MP3 file."""
    try:
        audio = MP3(mp3_file, ID3=ID3)

        # Add ID3 tag if not present
        if not audio.tags:
            audio.tags = ID3()

        # Set metadata
        audio.tags.add(TIT2(encoding=3, text=title))  # Title
        audio.tags.add(TPE1(encoding=3, text=artist))  # Artist
        audio.tags.add(TALB(encoding=3, text=album))  # Album

        # Save metadata
        audio.save()

        print(f"✅ Metadata added: Title='{title}', Artist='{artist}', Album='{album}'")
    except Exception as e:
        print(f"❌ Metadata Error: {e}")

@app.route('/download', methods=['GET'])
def download_song():
    """Handles API request to download a song as MP3 with metadata."""
    song_name = request.args.get('song')

    if not song_name:
        return jsonify({"error": "Please provide a song name"}), 400

    video_details = get_video_details(song_name)

    if not video_details:
        return jsonify({"error": "No video found for the given song name"}), 404

    print(f"🔗 Found Video: {video_details['video_url']}")

    mp3_file = download_audio(video_details['video_url'], video_details['title'])

    if not mp3_file:
        return jsonify({"error": "Error downloading audio"}), 500

    # Add metadata (Title, Artist, Album)
    add_metadata(mp3_file, video_details['title'], video_details['artist'], video_details['album'])

    return send_file(mp3_file, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
