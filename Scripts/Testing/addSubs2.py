import os
import time
import requests
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import ImageFont, ImageDraw, Image

# AssemblyAI API key
ASSEMBLYAI_API_KEY = 'b4d51b033b3e4219bd8773813a34149f'  # Replace with your actual API key
VIDEO_PATH = "aita_TEST2.mp4"  # Update with your actual video path
FONT_PATH = "Fonts/Gilroy-Bold.ttf"  # Path to the Gilroy-Bold font

def transcribe_audio(audio_file):
    # Upload audio file to AssemblyAI
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    with open(audio_file, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
    audio_url = upload_response.json()['upload_url']

    # Request transcription
    transcription_request = {
        'audio_url': audio_url,
        'language_model': 'assemblyai_default',
        'punctuate': True
    }
    response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcription_request, headers=headers)
    transcript_id = response.json()['id']

    # Wait for the transcription to complete
    while True:
        time.sleep(5)  # Check every 5 seconds
        transcript_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        if transcript_response.json()['status'] == 'completed':
            break

    return transcript_response.json()['text'], transcript_response.json()['words']

def create_srt(words, srt_file_path):
    with open(srt_file_path, 'w') as srt_file:
        for index, word_info in enumerate(words):
            start = word_info['start']
            end = word_info['end']
            text = word_info['text'].replace(',', '').replace('.', '')  # Remove commas and periods
            srt_file.write(f"{index + 1}\n")
            srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
            srt_file.write(f"{text}\n\n")

def format_time(milliseconds):
    """Convert milliseconds to SRT time format."""
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def draw_text_with_outline(text, font, size):
    """Create an image with outlined text centered in the video."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Calculate text size and position for centering using textbbox
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (size[0] - text_width) // 2
    text_y = (size[1] - text_height) // 2

    outline_color = "black"
    outline_thickness = 2

    # Draw the outline
    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((text_x + dx, text_y + dy), text, font=font, fill=outline_color)

    # Draw the main text
    draw.text((text_x, text_y), text, font=font, fill='yellow')

    return img

def burn_subtitles(video_path, srt_file_path):
    video = VideoFileClip(video_path)

    # Load font
    font = ImageFont.truetype(FONT_PATH, 34)  # Font size 34
    subtitles = []

    with open(srt_file_path, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 4):
            time_range = lines[i + 1].strip().split(" --> ")
            start_time = convert_time_to_seconds(time_range[0])
            end_time = convert_time_to_seconds(time_range[1])
            text = lines[i + 2].strip()

            # Create an image with outlined text
            text_image = draw_text_with_outline(text, font, video.size)
            text_image_path = "temp_subtitle.png"  # Temporary file path
            text_image.save(text_image_path)

            # Create a TextClip using the image
            text_clip = (ImageClip(text_image_path)
                         .set_duration(end_time - start_time)
                         .set_start(start_time)
                         .set_position(('center', 'center')))  # Position in the center

            subtitles.append(text_clip)

    # Combine video and subtitles
    final_video = CompositeVideoClip([video] + subtitles)
    output_video_path = os.path.splitext(video_path)[0] + "_WITH_SUBS.mp4"
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    # Cleanup temporary file
    if os.path.exists(text_image_path):
        os.remove(text_image_path)

    print(f'Video created: {output_video_path}')


def convert_time_to_seconds(time_str):
    """Convert SRT time format to seconds."""
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

def main():
    audio_path = os.path.splitext(VIDEO_PATH)[0] + ".mp3"

    # Extract audio from video using moviepy
    video = VideoFileClip(VIDEO_PATH)
    video.audio.write_audiofile(audio_path, codec='libmp3lame')

    # Transcribe audio and get words
    text, words = transcribe_audio(audio_path)

    # Create SRT file
    srt_file_path = os.path.splitext(VIDEO_PATH)[0] + ".srt"
    create_srt(words, srt_file_path)

    # Burn subtitles into video
    burn_subtitles(VIDEO_PATH, srt_file_path)

    # Clean up
    os.remove(audio_path)
    os.remove(srt_file_path)

if __name__ == "__main__":
    main()
