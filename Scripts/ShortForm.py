'''
import os
import time
import random
import asyncio
import edge_tts
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from pydub import AudioSegment
from PIL import Image, ImageFont, ImageDraw  # Add Image to the import statement


# Constants
TEXT_FILE_PATH = 'TXT/script.txt'
OUTPUT_AUDIO = 'Moutput.mp3'

VIDEO_FILE_OPTIONS = [
    'ShortFormGen/Content/GTA/gta-1.mp4',
    'ShortFormGen/Content/GTA/gta-2.mp4',
    'ShortFormGen/Content/MC/mc-1.mp4',
    'ShortFormGen/Content/MC/mc-2.mp4'
]
VIDEO_FILE_PATH = random.choice(VIDEO_FILE_OPTIONS)  # Randomly select a video file

#VIDEO_FILE_PATH = 'ShortFormGen/Content/GTA/gta-1.mp4'
OUTPUT_VIDEO_FILE_PATH = os.path.join(os.getcwd(), 'AITA.mp4')
ASSEMBLYAI_API_KEY = 'b4d51b033b3e4219bd8773813a34149f'  # Replace with your actual API key
FONT_PATH = 'Fonts/Gilroy-Bold.ttf'  # Path to the Gilroy-Bold font

# Voice Selection
VOICES = ['en-GB-RyanNeural', 'en-US-JennyNeural', 'en-GB-LibbyNeural']  # Choose your preferred voice

# Generate TTS using edge_tts
async def generate_tts(text):
    voice = VOICES[2]
    communicate = edge_tts.Communicate(text, voice, rate='+15%')
    await communicate.save(OUTPUT_AUDIO)
    print(f'Audio saved to {OUTPUT_AUDIO}')

# Get audio duration
def get_audio_duration(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

# Extract random video clip
def extract_random_video_clip(video_file_path, duration):
    video = VideoFileClip(video_file_path)
    max_start_time = video.duration - duration
    if max_start_time <= 0:
        raise ValueError("The video is shorter than the audio duration.")
    start_time = random.uniform(0, max_start_time)
    print(f'Selected random start time: {start_time}, Duration: {duration}')
    return video.subclip(start_time, start_time + duration)

# Crop video to vertical format
def crop_to_vertical(video_clip):
    target_aspect_ratio = 9 / 16
    original_width, original_height = video_clip.size
    new_width = int(original_height * target_aspect_ratio)

    if original_width > new_width:
        x_center = original_width // 2
        x1 = x_center - new_width // 2
        x2 = x_center + new_width // 2
        return video_clip.crop(x1=x1, x2=x2)
    else:
        raise ValueError("The video is too narrow to be cropped to a vertical format.")

# Transcribe audio using AssemblyAI
def transcribe_audio(audio_file):
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    with open(audio_file, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
    audio_url = upload_response.json()['upload_url']
    
    transcription_request = {'audio_url': audio_url, 'language_model': 'assemblyai_default', 'punctuate': True}
    response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcription_request, headers=headers)
    transcript_id = response.json()['id']
    
    while True:
        time.sleep(5)
        transcript_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        if transcript_response.json()['status'] == 'completed':
            break
    return transcript_response.json()['text'], transcript_response.json()['words']

# Create .srt subtitle file
def create_srt(words, srt_file_path):
    with open(srt_file_path, 'w') as srt_file:
        for index, word_info in enumerate(words):
            start = word_info['start']
            end = word_info['end']
            text = word_info['text'].replace(',', '').replace('.', '')  # Remove commas and periods
            srt_file.write(f"{index + 1}\n")
            srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
            srt_file.write(f"{text}\n\n")

# Format time for .srt file
def format_time(milliseconds):
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

# Draw text with an outline
def draw_text_with_outline(text, font, size):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size[0] - text_width) // 2
    text_y = (size[1] - text_height) // 2
    outline_color = "black"
    outline_thickness = 2

    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((text_x + dx, text_y + dy), text, font=font, fill=outline_color)

    draw.text((text_x, text_y), text, font=font, fill='yellow')
    return img

# Burn subtitles into video
def burn_subtitles(video_path, srt_file_path):
    video = VideoFileClip(video_path)
    font = ImageFont.truetype(FONT_PATH, 34)
    subtitles = []

    with open(srt_file_path, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 4):
            time_range = lines[i + 1].strip().split(" --> ")
            start_time = convert_time_to_seconds(time_range[0])
            end_time = convert_time_to_seconds(time_range[1])
            text = lines[i + 2].strip()

            text_image = draw_text_with_outline(text, font, video.size)
            text_image_path = "temp_subtitle.png"
            text_image.save(text_image_path)

            text_clip = (ImageClip(text_image_path)
                         .set_duration(end_time - start_time)
                         .set_start(start_time)
                         .set_position(('center', 'center')))
            subtitles.append(text_clip)

    final_video = CompositeVideoClip([video] + subtitles)
    final_output_path = os.path.splitext(video_path)[0] + "_WITH_SUBS.mp4"

    final_video.write_videofile(final_output_path, codec="libx264", audio_codec="aac", bitrate="5000k", preset="slow", fps=30, threads=4, ffmpeg_params=["-crf", "18"])
    print(f'Video with subtitles created: {final_output_path}')

    if os.path.exists(text_image_path):
        os.remove(text_image_path)

# Convert subtitle time to seconds
def convert_time_to_seconds(time_str):
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

# Main function
async def main():
    print('Text to Speech Test')
    print('-------------------')
    print(f"Current working directory: {os.getcwd()}")
    print('-------------------')
    print('Text file path:', TEXT_FILE_PATH)

    # Load text from the file
    with open(TEXT_FILE_PATH, 'r', encoding='utf-8') as file:
        text = file.read()

    # Generate TTS audio
    await generate_tts(text)

    # Get the audio duration
    audio_duration = get_audio_duration(OUTPUT_AUDIO)
    print(f"Audio duration: {audio_duration} seconds")

    # Extract a random video clip of the same length as the audio
    video_clip = extract_random_video_clip(VIDEO_FILE_PATH, audio_duration)
    video_clip = crop_to_vertical(video_clip)
    
    # Sync the audio with the video clip
    audio_clip = AudioFileClip(OUTPUT_AUDIO)
    video_clip = video_clip.set_audio(audio_clip)
    
    # Save the video file
    video_clip.write_videofile(OUTPUT_VIDEO_FILE_PATH, codec="libx264", audio_codec="aac", bitrate="5000k", preset="slow", fps=30, threads=4, ffmpeg_params=["-crf", "18"])
    print(f"Video created: {OUTPUT_VIDEO_FILE_PATH}")

    # Transcribe the audio and create an .srt file
    text, words = transcribe_audio(OUTPUT_AUDIO)
    srt_file_path = os.path.splitext(VIDEO_FILE_PATH)[0] + ".srt"
    create_srt(words, srt_file_path)
    
    # Burn subtitles into the video
    burn_subtitles(OUTPUT_VIDEO_FILE_PATH, srt_file_path)

    # Clean up generated files
    os.remove(OUTPUT_AUDIO)
    os.remove(srt_file_path)
'''

import os
import time
import re
import random
import asyncio
import edge_tts
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
from pydub import AudioSegment
from PIL import Image, ImageFont, ImageDraw

# Constants
SCRIPTS = [
    'TXT/script-1.txt',
    'TXT/script-2.txt',
    'TXT/script-3.txt',
    'TXT/script-4.txt',
    'TXT/script-5.txt'
]
OUTPUT_AUDIO_PREFIX = 'Moutput'
OUTPUT_VIDEO_PREFIX = 'AITA'

VIDEO_FILE_OPTIONS = [
    'ShortFormGen/Content/GTA/gta-1.mp4',
    'ShortFormGen/Content/GTA/gta-2.mp4',
    'ShortFormGen/Content/MC/mc-1.mp4',
    'ShortFormGen/Content/MC/mc-2.mp4'
]

ASSEMBLYAI_API_KEY = 'b4d51b033b3e4219bd8773813a34149f'  # Replace with your actual API key
FONT_PATH = 'Fonts/Gilroy-Bold.ttf'  # Path to the Gilroy-Bold font

# Voice Selection
VOICES = ['en-GB-RyanNeural', 'en-US-JennyNeural', 'en-GB-LibbyNeural']

# Generate TTS using edge_tts
async def generate_tts(text, output_audio, voice):
    communicate = edge_tts.Communicate(text, voice, rate='+15%')
    await communicate.save(output_audio)
    print(f'Audio saved to {output_audio}')

# Get audio duration
def get_audio_duration(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)
    return len(audio) / 1000  # Convert milliseconds to seconds

# Extract random video clip
def extract_random_video_clip(video_file_path, duration):
    video = VideoFileClip(video_file_path)
    max_start_time = video.duration - duration
    if max_start_time <= 0:
        raise ValueError("The video is shorter than the audio duration.")
    start_time = random.uniform(0, max_start_time)
    print(f'Selected random start time: {start_time}, Duration: {duration}')
    return video.subclip(start_time, start_time + duration)

# Crop video to vertical format
def crop_to_vertical(video_clip):
    target_aspect_ratio = 9 / 16
    original_width, original_height = video_clip.size
    new_width = int(original_height * target_aspect_ratio)

    if original_width > new_width:
        x_center = original_width // 2
        x1 = x_center - new_width // 2
        x2 = x_center + new_width // 2
        return video_clip.crop(x1=x1, x2=x2)
    else:
        raise ValueError("The video is too narrow to be cropped to a vertical format.")

# Function to extract the title and replace "AM I THE ASSHOLE" with "AITA"
def extract_title_from_script(script_path):
    with open(script_path, 'r', encoding='utf-8') as file:
        text = file.read()
    
    # Find the first question (i.e., the first occurrence of "?")
    match = re.search(r'.*?\?', text)
    if match:
        # Extract the text up to the first "?" and replace "AM I THE ASSHOLE" with "AITA"
        title = match.group(0).strip()
        title = title.replace("AM I THE ASSHOLE", "AITA", 1)
        return title
    else:
        # Default title if no "?" is found
        return "Untitled Video"
    

# Transcribe audio using AssemblyAI
def transcribe_audio(audio_file):
    headers = {'authorization': ASSEMBLYAI_API_KEY}
    with open(audio_file, 'rb') as f:
        upload_response = requests.post('https://api.assemblyai.com/v2/upload', headers=headers, data=f)
    audio_url = upload_response.json()['upload_url']
    
    transcription_request = {'audio_url': audio_url, 'language_model': 'assemblyai_default', 'punctuate': True}
    response = requests.post('https://api.assemblyai.com/v2/transcript', json=transcription_request, headers=headers)
    transcript_id = response.json()['id']
    
    while True:
        time.sleep(5)
        transcript_response = requests.get(f'https://api.assemblyai.com/v2/transcript/{transcript_id}', headers=headers)
        if transcript_response.json()['status'] == 'completed':
            break
    return transcript_response.json()['text'], transcript_response.json()['words']

# Create .srt subtitle file
def create_srt(words, srt_file_path):
    with open(srt_file_path, 'w') as srt_file:
        for index, word_info in enumerate(words):
            start = word_info['start']
            end = word_info['end']
            text = word_info['text'].replace(',', '').replace('.', '')  # Remove commas and periods
            srt_file.write(f"{index + 1}\n")
            srt_file.write(f"{format_time(start)} --> {format_time(end)}\n")
            srt_file.write(f"{text}\n\n")

# Format time for .srt file
def format_time(milliseconds):
    total_seconds = milliseconds / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds - int(total_seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

# Draw text with an outline
def draw_text_with_outline(text, font, size):
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size[0] - text_width) // 2
    text_y = (size[1] - text_height) // 2
    outline_color = "black"
    outline_thickness = 2

    for dx in range(-outline_thickness, outline_thickness + 1):
        for dy in range(-outline_thickness, outline_thickness + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((text_x + dx, text_y + dy), text, font=font, fill=outline_color)

    draw.text((text_x, text_y), text, font=font, fill='yellow')
    return img

# Burn subtitles into video
def burn_subtitles(video_path, srt_file_path):
    video = VideoFileClip(video_path)
    font = ImageFont.truetype(FONT_PATH, 34)
    subtitles = []

    with open(srt_file_path, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 4):
            time_range = lines[i + 1].strip().split(" --> ")
            start_time = convert_time_to_seconds(time_range[0])
            end_time = convert_time_to_seconds(time_range[1])
            text = lines[i + 2].strip()

            text_image = draw_text_with_outline(text, font, video.size)
            text_image_path = "temp_subtitle.png"
            text_image.save(text_image_path)

            text_clip = (ImageClip(text_image_path)
                         .set_duration(end_time - start_time)
                         .set_start(start_time)
                         .set_position(('center', 'center')))
            subtitles.append(text_clip)

    final_video = CompositeVideoClip([video] + subtitles)
    final_output_path = os.path.splitext(video_path)[0] + "_WITH_SUBS.mp4"

    final_video.write_videofile(final_output_path, codec="libx264", audio_codec="aac", bitrate="5000k", preset="slow", fps=30, threads=4, ffmpeg_params=["-crf", "18"])
    print(f'Video with subtitles created: {final_output_path}')

    if os.path.exists(text_image_path):
        os.remove(text_image_path)

# Convert subtitle time to seconds
def convert_time_to_seconds(time_str):
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000

# Main function to bulk create videos
async def bulk_create_videos():

    print('Text to Speech Test')
    print('-------------------')

    voice_choice = [0,0,0,2,0]

    for i, script_path in enumerate(SCRIPTS):
        print(f'Processing video {i + 1}...')
        
        # Load text from the file
        with open(script_path, 'r', encoding='utf-8') as file:
            text = file.read()

        # Set paths for audio and video output
        output_audio = f"{OUTPUT_AUDIO_PREFIX}_{i + 1}.mp3"
        output_video = f"{OUTPUT_VIDEO_PREFIX}_{i + 1}.mp4"
        
        # Choose a voice for TTS (ask for user input or set default)
        selected_voice = VOICES[voice_choice[i]]

        # Generate TTS audio
        await generate_tts(text, output_audio, selected_voice)

        # Get the audio duration
        audio_duration = get_audio_duration(output_audio)
        print(f"Audio duration for video {i + 1}: {audio_duration} seconds")

        # Extract a random video clip of the same length as the audio
        video_file_path = random.choice(VIDEO_FILE_OPTIONS)
        video_clip = extract_random_video_clip(video_file_path, audio_duration)

        # Crop the video to vertical format
        cropped_video = crop_to_vertical(video_clip)

        # Add audio to the video
        audio_clip = AudioFileClip(output_audio)
        final_video = cropped_video.set_audio(audio_clip)
        final_video.write_videofile(output_video, codec="libx264", audio_codec="aac", bitrate="5000k", preset="slow", fps=30, threads=4, ffmpeg_params=["-crf", "18"])

        # Transcribe the audio and generate the subtitle file
        transcript, words = transcribe_audio(output_audio)
        srt_file_path = f"{OUTPUT_AUDIO_PREFIX}_{i + 1}.srt"
        create_srt(words, srt_file_path)

        # Burn the subtitles into the video
        burn_subtitles(output_video, srt_file_path)

        title = extract_title_from_script(script_path)
        print(f'Title for video {i + 1}: {title}')

        print(f'Video {i + 1} completed!')
        print('-------------------')
        print('Deleting temporary files...')

        # Clean up generated files
        print(f'Deleting {output_audio}...')
        os.remove(output_audio)
        print(f'Deleting {srt_file_path}...')
        os.remove(srt_file_path)
        os.remove(f'AITA_{i + 1}.mp4')
        print('Temporary files deleted!')
        print('-------------------')



# Run the script
if __name__ == "__main__":
    asyncio.run(bulk_create_videos())
