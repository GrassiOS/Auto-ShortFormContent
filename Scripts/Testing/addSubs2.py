import os
import time
import requests
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from tqdm import tqdm

# AssemblyAI API key
ASSEMBLYAI_API_KEY = 'b4d51b033b3e4219bd8773813a34149f'  # Replace with your actual API key
VIDEO_PATH = "aita_TEST2.mp4"  # Update with your actual video path

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

def burn_subtitles(video_path, srt_file_path):
    video = VideoFileClip(video_path)
    
    # Read SRT file and create TextClips for subtitles
    subtitles = []
    with open(srt_file_path, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 4):
            index = lines[i].strip()
            time_range = lines[i + 1].strip().split(" --> ")
            start_time = convert_time_to_seconds(time_range[0])
            end_time = convert_time_to_seconds(time_range[1])
            text = lines[i + 2].strip()

            # Create a TextClip for each subtitle without background
            subtitle_clip = TextClip(text, fontsize=34, color='yellow', size=video.size)
            subtitle_clip = subtitle_clip.set_position('bottom').set_duration(end_time - start_time).set_start(start_time)
            subtitles.append(subtitle_clip)

    # Combine video and subtitles
    final_video = CompositeVideoClip([video] + subtitles)
    output_video_path = os.path.splitext(video_path)[0] + "_WITH_SUBS.mp4"
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')
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
