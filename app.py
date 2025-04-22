# from flask import Flask, request, send_file, render_template
# from yt_dlp import YoutubeDL
# import instaloader
# import os
# from io import BytesIO
# import re
# import subprocess
# import shutil
# import time
# import logging
# import requests

# app = Flask(__name__)

# # Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # Store video info globally (for simplicity)
# video_info = {}

# # Use /tmp/static for Vercel compatibility
# STATIC_DIR = "/tmp/static" if os.getenv("VERCEL") else "static"

# # Ensure static directory exists
# if not os.path.exists(STATIC_DIR):
#     os.makedirs(STATIC_DIR)

# # Initialize Instaloader with a user agent
# L = instaloader.Instaloader(download_videos=True, download_pictures=False, download_video_thumbnails=True)
# L.context._session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

# def is_instagram_url(url):
#     """Check if the URL is an Instagram Reel URL."""
#     return bool(re.match(r"https?://(www\.)?instagram\.com/reel/.*", url))

# def is_facebook_reel_url(url):
#     """Check if the URL is a Facebook Reel URL."""
#     return bool(re.match(r"https?://(www\.)?(facebook|fb)\.com/reel/.*", url))

# def sanitize_filename(filename):
#     """Sanitize the filename by removing invalid characters and newlines."""
#     filename = re.sub(r'\s+', ' ', filename.strip())
#     filename = re.sub(r'[<>:"/\\|?*]', '', filename)
#     return filename[:100]

# def download_thumbnail(url, output_path):
#     """Download the thumbnail from a URL to the specified path."""
#     try:
#         response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
#         if response.status_code == 200:
#             with open(output_path, 'wb') as f:
#                 for chunk in response.iter_content(chunk_size=8192):
#                     if chunk:
#                         f.write(chunk)
#             return True
#         else:
#             logger.warning(f"Failed to download thumbnail: {url}, status code: {response.status_code}")
#             return False
#     except Exception as e:
#         logger.error(f"Error downloading thumbnail: {e}")
#         return False

# def reencode_video(input_path, output_path, resolution):
#     """Re-encode video to the specified resolution using ffmpeg."""
#     width, height = resolution.split('x')
#     try:
#         subprocess.run([
#             'ffmpeg',
#             '-i', input_path,
#             '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
#             '-c:v', 'libx264',
#             '-b:v', '1M',
#             '-c:a', 'aac',
#             output_path
#         ], check=True)
#         return True
#     except Exception as e:
#         logger.error(f"Error re-encoding video: {e}")
#         return False

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/fetch', methods=['POST'])
# def fetch():
#     global video_info
#     url = request.form['url']
#     try:
#         if is_instagram_url(url):
#             # Handle Instagram Reel
#             shortcode = url.split('/reel/')[1].split('/')[0]
#             logger.debug(f"Fetching Instagram Reel with shortcode: {shortcode}")
#             post = instaloader.Post.from_shortcode(L.context, shortcode)
            
#             # Clean up any existing temp_reel directory
#             if os.path.exists("temp_reel"):
#                 shutil.rmtree("temp_reel", ignore_errors=True)
            
#             # Download the Reel (including video)
#             L.download_post(post, target="temp_reel")
            
#             # Find the downloaded video file
#             video_path = None
#             for file in os.listdir("temp_reel"):
#                 if file.endswith(".mp4"):
#                     video_path = os.path.join("temp_reel", file)
#             if not video_path:
#                 logger.error("No MP4 file found in temp_reel directory")
#                 return "Error: Could not find downloaded Reel video.", 500

#             logger.debug(f"Found video file: {video_path}")

#             # Try to fetch the thumbnail manually
#             thumbnail_path = None
#             thumbnail_url = None
#             if post.is_video:
#                 # Instagram Reels typically use the display_url or a thumbnail URL in the post's metadata
#                 thumbnail_url = post._asdict().get('thumbnail_url', post.url)
#                 logger.debug(f"Thumbnail URL from metadata: {thumbnail_url}")
#                 # Download the thumbnail manually
#                 thumbnail_filename = f"{shortcode}_thumbnail.jpg"
#                 thumbnail_path = os.path.join(STATIC_DIR, thumbnail_filename)
#                 if download_thumbnail(thumbnail_url, thumbnail_path):
#                     logger.debug(f"Successfully downloaded thumbnail to: {thumbnail_path}")
#                 else:
#                     logger.warning("Failed to download thumbnail manually")
#                     thumbnail_path = ''
#             else:
#                 logger.warning("Post is not a video, no thumbnail available")
#                 thumbnail_path = ''

#             # Define available resolutions (for local testing with ffmpeg)
#             resolutions = ['360x640', '480x854', '720x1280']
#             video_formats = [
#                 {
#                     'format_id': f'instagram_reel_{res}',
#                     'resolution': res.split('x')[1] + 'p',
#                     'ext': 'mp4',
#                     'fps': 'Unknown'
#                 } for res in resolutions
#             ]
#             # Add original resolution option
#             video_formats.append({
#                 'format_id': 'instagram_reel_original',
#                 'resolution': 'Original',
#                 'ext': 'mp4',
#                 'fps': 'Unknown'
#             })
#             audio_formats = []

#             # Use caption or username as title if caption is not available
#             title = post.caption if post.caption else f"Reel by {post.owner_username}"
#             if not title:
#                 title = "Instagram Reel"
#             sanitized_title = sanitize_filename(title)

#             video_info = {
#                 'title': title,
#                 'sanitized_title': sanitized_title,
#                 'thumbnail': os.path.basename(thumbnail_path) if thumbnail_path else '',
#                 'thumbnail_type': 'local' if thumbnail_path else 'none',  # Local file for Instagram
#                 'video_formats': video_formats,
#                 'audio_formats': audio_formats,
#                 'url': url,
#                 'video_path': video_path
#             }
#         else:
#             # Handle YouTube or Facebook Reel
#             ydl_opts = {
#                 'format': 'bestvideo+bestaudio/best',
#                 'listformats': True,
#             }
#             with YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(url, download=False)
#                 video_formats = [
#                     {
#                         'format_id': fmt['format_id'],
#                         'resolution': fmt.get('height', 'Unknown'),
#                         'ext': fmt['ext'],
#                         'fps': fmt.get('fps', 'Unknown')
#                     }
#                     for fmt in info['formats']
#                     if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none' and fmt.get('ext') == 'mp4'
#                 ]
#                 audio_formats = [
#                     {
#                         'format_id': fmt['format_id'],
#                         'abr': fmt.get('abr', 'Unknown'),
#                         'ext': fmt['ext']
#                     }
#                     for fmt in info['formats']
#                     if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none' and fmt.get('ext') in ['m4a', 'mp3']
#                 ]

#                 video_formats = sorted(
#                     video_formats,
#                     key=lambda x: int(x['resolution']) if x['resolution'] != 'Unknown' else 0,
#                     reverse=True
#                 )

#                 # Use uploader or description as fallback title if needed
#                 title = info.get('title', 'Untitled Video')
#                 if not title or title == 'Untitled Video':
#                     title = info.get('uploader', 'Facebook Reel') + " Reel"
#                 sanitized_title = sanitize_filename(title)

#                 # Fetch the thumbnail URL and test accessibility
#                 thumbnail_url = info.get('thumbnail', '')
#                 thumbnail_type = 'none'
#                 if thumbnail_url:
#                     try:
#                         # Use a GET request instead of HEAD to better handle redirects
#                         response = requests.get(thumbnail_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
#                         if response.status_code == 200:
#                             thumbnail_type = 'remote'
#                             logger.debug(f"YouTube/Facebook thumbnail URL is accessible: {thumbnail_url}")
#                         else:
#                             logger.warning(f"Thumbnail URL not accessible: {thumbnail_url}, status code: {response.status_code}")
#                             thumbnail_url = ''
#                     except Exception as e:
#                         logger.error(f"Error accessing thumbnail URL: {e}")
#                         thumbnail_url = ''

#                 video_info = {
#                     'title': title,
#                     'sanitized_title': sanitized_title,
#                     'thumbnail': thumbnail_url,
#                     'thumbnail_type': thumbnail_type,  # Remote URL for YouTube/Facebook
#                     'video_formats': video_formats,
#                     'audio_formats': audio_formats,
#                     'url': url
#                 }

#         return render_template('results.html', video=video_info)
#     except Exception as e:
#         logger.error(f"Error in fetch route: {str(e)}")
#         return f"Error: {str(e)}", 500

# @app.route('/download/<format_id>')
# def download(format_id):
#     global video_info
#     try:
#         logger.debug(f"Starting download for format_id: {format_id}")
#         if 'instagram_reel' in format_id:
#             # Handle Instagram Reel download
#             video_path = video_info.get('video_path')
#             logger.debug(f"Video path: {video_path}")
#             if not video_path or not os.path.exists(video_path):
#                 logger.error("Video file not found at the specified path")
#                 return "Error: Video file not found.", 404

#             # Wait briefly to ensure file is fully written
#             time.sleep(1)

#             if format_id == 'instagram_reel_original':
#                 # Download original resolution
#                 buffer = BytesIO()
#                 with open(video_path, 'rb') as f:
#                     buffer.write(f.read())
#                 buffer.seek(0)

#                 # Clean up
#                 logger.debug("Cleaning up temp_reel directory")
#                 shutil.rmtree("temp_reel", ignore_errors=True)

#                 # Clean up static directory (remove thumbnail)
#                 if video_info.get('thumbnail') and video_info.get('thumbnail_type') == 'local':
#                     thumbnail_static_path = os.path.join(STATIC_DIR, video_info['thumbnail'])
#                     if os.path.exists(thumbnail_static_path):
#                         os.remove(thumbnail_static_path)
#                         logger.debug(f"Removed thumbnail from static directory: {thumbnail_static_path}")

#                 logger.debug("Sending file to client")
#                 return send_file(
#                     buffer,
#                     as_attachment=True,
#                     download_name=f"{video_info['sanitized_title']}.mp4",
#                     mimetype="video/mp4"
#                 )
#             else:
#                 # Re-encode to desired resolution (requires ffmpeg)
#                 resolution = format_id.split('_')[-1]
#                 output_path = "temp_reel/output.mp4"
#                 if reencode_video(video_path, output_path, resolution):
#                     buffer = BytesIO()
#                     with open(output_path, 'rb') as f:
#                         buffer.write(f.read())
#                     buffer.seek(0)

#                     # Clean up
#                     logger.debug("Cleaning up temp_reel directory after re-encoding")
#                     shutil.rmtree("temp_reel", ignore_errors=True)

#                     # Clean up static directory (remove thumbnail)
#                     if video_info.get('thumbnail') and video_info.get('thumbnail_type') == 'local':
#                         thumbnail_static_path = os.path.join(STATIC_DIR, video_info['thumbnail'])
#                         if os.path.exists(thumbnail_static_path):
#                             os.remove(thumbnail_static_path)
#                             logger.debug(f"Removed thumbnail from static directory: {thumbnail_static_path}")

#                     logger.debug("Sending re-encoded file to client")
#                     return send_file(
#                         buffer,
#                         as_attachment=True,
#                         download_name=f"{video_info['sanitized_title']}_{resolution.split('x')[1]}p.mp4",
#                         mimetype="video/mp4"
#                     )
#                 else:
#                     logger.error("Failed to re-encode video")
#                     return "Error: Failed to re-encode video. Try original resolution.", 500
#         else:
#             # Handle YouTube or Facebook Reel download
#             ydl_opts = {
#                 'format': format_id,
#                 'simulate': True,  # Don't download, just get the URL
#             }
#             with YoutubeDL(ydl_opts) as ydl:
#                 info = ydl.extract_info(video_info['url'], download=False)
#                 video_url = info['url']  # Get the direct stream URL

#             # Stream the video directly into memory
#             logger.debug(f"Fetching video stream from: {video_url}")
#             response = requests.get(video_url, stream=True)
#             if response.status_code != 200:
#                 logger.error(f"Failed to fetch video stream: {response.status_code}")
#                 return "Error: Could not fetch video stream.", 500

#             buffer = BytesIO()
#             for chunk in response.iter_content(chunk_size=8192):
#                 if chunk:
#                     buffer.write(chunk)
#             buffer.seek(0)

#             ext = next((fmt['ext'] for fmt in video_info['video_formats'] + video_info['audio_formats'] if fmt['format_id'] == format_id), 'mp4')
#             logger.debug("Sending file to client")
#             return send_file(
#                 buffer,
#                 as_attachment=True,
#                 download_name=f"{video_info['sanitized_title']}.{ext}",
#                 mimetype=f"video/{ext}" if ext == 'mp4' else f"audio/{ext}"
#             )
#     except Exception as e:
#         logger.error(f"Error in download route: {str(e)}")
#         return f"Error: {str(e)}", 500

# if __name__ == '__main__':
#     app.run(debug=True)

from flask import Flask, request, send_file, render_template
from yt_dlp import YoutubeDL
import instaloader
import os
from io import BytesIO
import re
import subprocess
import shutil
import time
import logging
import requests

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Store video info globally (for simplicity)
video_info = {}

# Use /tmp/static for Vercel compatibility
STATIC_DIR = "/tmp/static" if os.getenv("VERCEL") else "static"

# Ensure static directory exists
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Initialize Instaloader with a user agent
L = instaloader.Instaloader(download_videos=True, download_pictures=False, download_video_thumbnails=True)
L.context._session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})

def is_instagram_url(url):
    """Check if the URL is an Instagram Reel URL."""
    return bool(re.match(r"https?://(www\.)?instagram\.com/reel/.*", url))

def is_facebook_reel_url(url):
    """Check if the URL is a Facebook Reel URL."""
    return bool(re.match(r"https?://(www\.)?(facebook|fb)\.com/reel/.*", url))

def sanitize_filename(filename):
    """Sanitize the filename by removing invalid characters and newlines."""
    filename = re.sub(r'\s+', ' ', filename.strip())
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    return filename[:100]

def download_thumbnail(url, output_path):
    """Download the thumbnail from a URL to the specified path."""
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        else:
            logger.warning(f"Failed to download thumbnail: {url}, status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error downloading thumbnail: {e}")
        return False

def reencode_video(input_path, output_path, resolution):
    """Re-encode video to the specified resolution using ffmpeg."""
    width, height = resolution.split('x')
    try:
        subprocess.run([
            'ffmpeg',
            '-i', input_path,
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-b:v', '1M',
            '-c:a', 'aac',
            output_path
        ], check=True)
        return True
    except Exception as e:
        logger.error(f"Error re-encoding video: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch():
    global video_info
    url = request.form['url']
    try:
        if is_instagram_url(url):
            # Handle Instagram Reel
            shortcode = url.split('/reel/')[1].split('/')[0]
            logger.debug(f"Fetching Instagram Reel with shortcode: {shortcode}")
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            # Clean up any existing temp_reel directory
            if os.path.exists("temp_reel"):
                shutil.rmtree("temp_reel", ignore_errors=True)
            
            # Download the Reel (including video)
            L.download_post(post, target="temp_reel")
            
            # Find the downloaded video file
            video_path = None
            for file in os.listdir("temp_reel"):
                if file.endswith(".mp4"):
                    video_path = os.path.join("temp_reel", file)
            if not video_path:
                logger.error("No MP4 file found in temp_reel directory")
                return "Error: Could not find downloaded Reel video.", 500

            logger.debug(f"Found video file: {video_path}")

            # Try to fetch the thumbnail manually
            thumbnail_path = None
            thumbnail_url = None
            if post.is_video:
                # Instagram Reels typically use the display_url or a thumbnail URL in the post's metadata
                thumbnail_url = post._asdict().get('thumbnail_url', post.url)
                logger.debug(f"Thumbnail URL from metadata: {thumbnail_url}")
                # Download the thumbnail manually
                thumbnail_filename = f"{shortcode}_thumbnail.jpg"
                thumbnail_path = os.path.join(STATIC_DIR, thumbnail_filename)
                if download_thumbnail(thumbnail_url, thumbnail_path):
                    logger.debug(f"Successfully downloaded thumbnail to: {thumbnail_path}")
                else:
                    logger.warning("Failed to download thumbnail manually")
                    thumbnail_path = ''
            else:
                logger.warning("Post is not a video, no thumbnail available")
                thumbnail_path = ''

            # Define available resolutions (for local testing with ffmpeg)
            resolutions = ['360x640', '480x854', '720x1280']
            video_formats = [
                {
                    'format_id': f'instagram_reel_{res}',
                    'resolution': res.split('x')[1] + 'p',
                    'ext': 'mp4',
                    'fps': 'Unknown'
                } for res in resolutions
            ]
            # Add original resolution option
            video_formats.append({
                'format_id': 'instagram_reel_original',
                'resolution': 'Original',
                'ext': 'mp4',
                'fps': 'Unknown'
            })
            audio_formats = []

            # Use caption or username as title if caption is not available
            title = post.caption if post.caption else f"Reel by {post.owner_username}"
            if not title:
                title = "Instagram Reel"
            sanitized_title = sanitize_filename(title)

            video_info = {
                'title': title,
                'sanitized_title': sanitized_title,
                'thumbnail': os.path.basename(thumbnail_path) if thumbnail_path else '',
                'thumbnail_type': 'local' if thumbnail_path else 'none',  # Local file for Instagram
                'video_formats': video_formats,
                'audio_formats': audio_formats,
                'url': url,
                'video_path': video_path
            }
        else:
            # Handle YouTube or Facebook Reel
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'listformats': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_formats = [
                    {
                        'format_id': fmt['format_id'],
                        'resolution': fmt.get('height', 'Unknown'),
                        'ext': fmt['ext'],
                        'fps': fmt.get('fps', 'Unknown')
                    }
                    for fmt in info['formats']
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none' and fmt.get('ext') == 'mp4'
                ]
                audio_formats = [
                    {
                        'format_id': fmt['format_id'],
                        'abr': fmt.get('abr', 'Unknown'),
                        'ext': fmt['ext']
                    }
                    for fmt in info['formats']
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none' and fmt.get('ext') in ['m4a', 'mp3']
                ]

                video_formats = sorted(
                    video_formats,
                    key=lambda x: int(x['resolution']) if x['resolution'] != 'Unknown' else 0,
                    reverse=True
                )

                # Use uploader or description as fallback title if needed
                title = info.get('title', 'Untitled Video')
                if not title or title == 'Untitled Video':
                    title = info.get('uploader', 'Facebook Reel') + " Reel"
                sanitized_title = sanitize_filename(title)

                # Fetch the thumbnail URL and test accessibility
                thumbnail_url = info.get('thumbnail', '')
                thumbnail_type = 'none'
                if thumbnail_url:
                    try:
                        # Use a GET request instead of HEAD to better handle redirects
                        response = requests.get(thumbnail_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
                        if response.status_code == 200:
                            thumbnail_type = 'remote'
                            logger.debug(f"YouTube/Facebook thumbnail URL is accessible: {thumbnail_url}")
                        else:
                            logger.warning(f"Thumbnail URL not accessible: {thumbnail_url}, status code: {response.status_code}")
                            thumbnail_url = ''
                    except Exception as e:
                        logger.error(f"Error accessing thumbnail URL: {e}")
                        thumbnail_url = ''

                video_info = {
                    'title': title,
                    'sanitized_title': sanitized_title,
                    'thumbnail': thumbnail_url,
                    'thumbnail_type': thumbnail_type,  # Remote URL for YouTube/Facebook
                    'video_formats': video_formats,
                    'audio_formats': audio_formats,
                    'url': url
                }

        return render_template('results.html', video=video_info)
    except Exception as e:
        logger.error(f"Error in fetch route: {str(e)}")
        return f"Error: {str(e)}", 500

@app.route('/download/<format_id>')
def download(format_id):
    global video_info
    try:
        logger.debug(f"Starting download for format_id: {format_id}")
        if 'instagram_reel' in format_id:
            # Handle Instagram Reel download
            video_path = video_info.get('video_path')
            logger.debug(f"Video path: {video_path}")
            if not video_path or not os.path.exists(video_path):
                logger.error("Video file not found at the specified path")
                return "Error: Video file not found.", 404

            # Wait briefly to ensure file is fully written
            time.sleep(1)

            if format_id == 'instagram_reel_original':
                # Download original resolution
                buffer = BytesIO()
                with open(video_path, 'rb') as f:
                    buffer.write(f.read())
                buffer.seek(0)

                # Clean up
                logger.debug("Cleaning up temp_reel directory")
                shutil.rmtree("temp_reel", ignore_errors=True)

                # Clean up static directory (remove thumbnail)
                if video_info.get('thumbnail') and video_info.get('thumbnail_type') == 'local':
                    thumbnail_static_path = os.path.join(STATIC_DIR, video_info['thumbnail'])
                    if os.path.exists(thumbnail_static_path):
                        os.remove(thumbnail_static_path)
                        logger.debug(f"Removed thumbnail from static directory: {thumbnail_static_path}")

                logger.debug("Sending file to client")
                return send_file(
                    buffer,
                    as_attachment=True,
                    download_name=f"{video_info['sanitized_title']}.mp4",
                    mimetype="video/mp4"
                )
            else:
                # Re-encode to desired resolution (requires ffmpeg)
                resolution = format_id.split('_')[-1]
                output_path = "temp_reel/output.mp4"
                if reencode_video(video_path, output_path, resolution):
                    buffer = BytesIO()
                    with open(output_path, 'rb') as f:
                        buffer.write(f.read())
                    buffer.seek(0)

                    # Clean up
                    logger.debug("Cleaning up temp_reel directory after re-encoding")
                    shutil.rmtree("temp_reel", ignore_errors=True)

                    # Clean up static directory (remove thumbnail)
                    if video_info.get('thumbnail') and video_info.get('thumbnail_type') == 'local':
                        thumbnail_static_path = os.path.join(STATIC_DIR, video_info['thumbnail'])
                        if os.path.exists(thumbnail_static_path):
                            os.remove(thumbnail_static_path)
                            logger.debug(f"Removed thumbnail from static directory: {thumbnail_static_path}")

                    logger.debug("Sending re-encoded file to client")
                    return send_file(
                        buffer,
                        as_attachment=True,
                        download_name=f"{video_info['sanitized_title']}_{resolution.split('x')[1]}p.mp4",
                        mimetype="video/mp4"
                    )
                else:
                    logger.error("Failed to re-encode video")
                    return "Error: Failed to re-encode video. Try original resolution.", 500
        else:
            # Handle YouTube or Facebook Reel download
            ydl_opts = {
                'format': format_id,
                'simulate': True,  # Don't download, just get the URL
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_info['url'], download=False)
                video_url = info['url']  # Get the direct stream URL

            # Stream the video directly into memory
            logger.debug(f"Fetching video stream from: {video_url}")
            response = requests.get(video_url, stream=True)
            if response.status_code != 200:
                logger.error(f"Failed to fetch video stream: {response.status_code}")
                return "Error: Could not fetch video stream.", 500

            buffer = BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)
            buffer.seek(0)

            ext = next((fmt['ext'] for fmt in video_info['video_formats'] + video_info['audio_formats'] if fmt['format_id'] == format_id), 'mp4')
            logger.debug("Sending file to client")
            return send_file(
                buffer,
                as_attachment=True,
                download_name=f"{video_info['sanitized_title']}.{ext}",
                mimetype=f"video/{ext}" if ext == 'mp4' else f"audio/{ext}"
            )
    except Exception as e:
        logger.error(f"Error in download route: {str(e)}")
        return f"Error: {str(e)}", 500

# Add the missing routes for About and Contact pages
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/favicon.ico')
def favicon_ico():
    return send_file(os.path.join(STATIC_DIR, 'favicon.png'), mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True)