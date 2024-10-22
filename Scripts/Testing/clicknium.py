from tiktok_uploader.upload import upload_video

video_path = 'AITA_2_WITH_SUBS.mp4'
description = 'this is my description'
cookies_path = 'Cookies/cookies.txt'

try:
    upload_video(video_path, description=description, cookies=cookies_path)
    print("Upload successful!")
except Exception as e:
    print(f"Failed to upload video: {e}")

#auth = AuthBackend(cookies='Cookies/cookies.txt')
#upload_videos(videos=videos, auth=auth)